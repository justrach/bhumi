use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::sync::Arc;
use tokio::sync::mpsc;
use serde_json::Value;
use futures_util::StreamExt;

mod anthropic;
mod gemini;
mod openai;

use gemini::{GeminiRequest, GeminiResponse};
use openai::OpenAIResponse;

// Response type to handle completions
#[pyclass]
struct LLMResponse {
    #[pyo3(get)]
    text: String,
    #[pyo3(get)]
    raw_response: String,
}

#[pyclass]
struct BhumiCore {
    sender: Arc<tokio::sync::Mutex<mpsc::Sender<String>>>,
    response_receiver: Arc<tokio::sync::Mutex<mpsc::Receiver<String>>>,
    runtime: Arc<tokio::runtime::Runtime>,
    #[pyo3(get)]
    max_concurrent: usize,
    active_requests: Arc<tokio::sync::RwLock<usize>>,
    debug: bool,
    client: Arc<reqwest::Client>,
    stream_buffer_size: usize,
    model: String,
    use_grounding: bool,
    provider: String,  // "anthropic", "gemini", "openai", "groq", or "sambanova"
}

#[pymethods]
impl BhumiCore {
    #[new]
    #[pyo3(signature = (max_concurrent, provider="anthropic", model="claude-3-sonnet-20240229", use_grounding=false, debug=false, stream_buffer_size=1000))]
    fn new(max_concurrent: usize, provider: &str, model: &str, use_grounding: bool, debug: bool, stream_buffer_size: usize) -> PyResult<Self> {
        let (request_tx, request_rx) = mpsc::channel::<String>(100_000);
        let (response_tx, response_rx) = mpsc::channel::<String>(100_000);
        
        let request_rx = Arc::new(tokio::sync::Mutex::new(request_rx));
        let sender = Arc::new(tokio::sync::Mutex::new(request_tx));
        let response_receiver = Arc::new(tokio::sync::Mutex::new(response_rx));
        let active_requests = Arc::new(tokio::sync::RwLock::new(0));
        let provider = provider.to_string();
        
        let runtime = Arc::new(
            tokio::runtime::Builder::new_multi_thread()
                .worker_threads(max_concurrent)
                .enable_all()
                .build()
                .unwrap()
        );
        let runtime_clone = runtime.clone();

        let client = reqwest::Client::builder()
            .pool_max_idle_per_host(max_concurrent * 2)
            .tcp_keepalive(Some(std::time::Duration::from_secs(30)))
            .tcp_nodelay(true)
            .pool_idle_timeout(Some(std::time::Duration::from_secs(60)))
            .http2_keep_alive_interval(std::time::Duration::from_secs(20))
            .http2_keep_alive_timeout(std::time::Duration::from_secs(30))
            .http2_adaptive_window(true)
            .pool_max_idle_per_host(100)
            .build()
            .unwrap();
        let client = Arc::new(client);

        // Spawn workers
        for worker_id in 0..max_concurrent {
            let request_rx = request_rx.clone();
            let response_tx = response_tx.clone();
            let active_requests = active_requests.clone();
            let client = client.clone();
            let debug = debug;
            let provider = provider.clone();
            let model = model.to_string();
            let use_grounding = use_grounding;
            
            runtime.spawn(async move {
                if debug {
                    println!("Starting worker {}", worker_id);
                }
                let mut buffer = Vec::with_capacity(32768);
                loop {
                    let request = {
                        let mut rx = request_rx.lock().await;
                        rx.recv().await
                    };

                    if debug {
                        println!("Worker {}: Received request", worker_id);
                    }

                    if let Some(request_str) = request {
                        {
                            let mut active = active_requests.write().await;
                            *active += 1;
                            if debug {
                                println!("Worker {}: Active requests: {}", worker_id, *active);
                            }
                        }

                        if let Ok(request_json) = serde_json::from_str::<Value>(&request_str) {
                            if let Some(api_key) = request_json
                                .get("_headers")
                                .and_then(|h| h.as_object())
                                .and_then(|h| h.get(if provider == "anthropic" { "x-api-key" } else { "Authorization" }))
                                .and_then(|k| k.as_str()) 
                            {
                                if debug {
                                    println!("Worker {}: Got API key", worker_id);
                                }
                                let response = match provider.as_str() {
                                    "anthropic" => {
                                        let mut request_body = request_json.clone();
                                        request_body.as_object_mut().map(|obj| obj.remove("_headers"));

                                        client.post("https://api.anthropic.com/v1/messages")
                                            .header("x-api-key", api_key)
                                            .header("anthropic-version", "2023-06-01")
                                            .header("content-type", "application/json")
                                            .header("connection", "keep-alive")
                                            .json(&request_body)
                                            .send()
                                            .await
                                    },
                                    "gemini" => {
                                        if debug {
                                            println!("Worker {}: Processing Gemini request, model: {}", worker_id, model);
                                        }
    
                                        let prompt = request_json
                                            .get("messages")
                                            .and_then(|m| m.as_array())
                                            .and_then(|m| m.first())
                                            .and_then(|m| m.get("content"))
                                            .and_then(|c| c.as_str())
                                            .unwrap_or_default();
    
                                        let gemini_request = GeminiRequest {
                                            contents: vec![gemini::Content {
                                                parts: vec![gemini::Part {
                                                    text: prompt.to_string(),
                                                }],
                                                role: Some("user".to_string()),
                                            }],
                                            tools: if use_grounding {
                                                Some(vec![gemini::Tool {
                                                    google_search: Some(gemini::GoogleSearch {}),
                                                }])
                                            } else {
                                                None
                                            },
                                        };
    
                                        let url = format!(
                                            "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}",
                                            model, api_key
                                        );
    
                                        if debug {
                                            println!("Worker {}: Sending request to API, size: {} bytes", worker_id, 
                                                serde_json::to_string(&gemini_request).unwrap_or_default().len());
                                        }
    
                                        let response = client.post(&url)
                                            .header("Content-Type", "application/json")
                                            .json(&gemini_request)
                                            .send()
                                            .await;
    
                                        if debug {
                                            if let Ok(resp) = &response {
                                                println!("Worker {}: Got response status: {}", worker_id, resp.status());
                                            }
                                        }
    
                                        response
                                    },
                                    "openai" => {
                                        if debug {
                                            println!("Worker {}: Processing OpenAI request", worker_id);
                                        }

                                        let prompt = request_json
                                            .get("messages")
                                            .and_then(|m| m.as_array())
                                            .and_then(|m| m.last())  // Get the last message (user's prompt)
                                            .and_then(|m| m.get("content"))
                                            .and_then(|c| c.as_str())
                                            .unwrap_or_default();

                                        let openai_request = serde_json::json!({
                                            "model": model,
                                            "messages": [
                                                {
                                                    "role": "system",
                                                    "content": "You are a helpful assistant"
                                                },
                                                {
                                                    "role": "user",
                                                    "content": prompt
                                                }
                                            ]
                                        });

                                        if debug {
                                            println!("Worker {}: Sending request to API", worker_id);
                                        }

                                        let response = client.post("https://api.openai.com/v1/chat/completions")
                                            .header("Authorization", format!("Bearer {}", api_key))
                                            .header("Content-Type", "application/json")
                                            .header("Accept", "application/json")
                                            .header("Connection", "keep-alive")
                                            .json(&openai_request)
                                            .send()
                                            .await;

                                        if debug {
                                            println!("Worker {}: Got API response: {:?}", worker_id, response.is_ok());
                                        }

                                        response
                                    },
                                    "groq" => {
                                        let mut request_body = request_json.clone();
                                        request_body.as_object_mut().map(|obj| obj.remove("_headers"));

                                        if debug {
                                            println!("Worker {}: Processing Groq request", worker_id);
                                            println!("Worker {}: Request body: {}", worker_id, 
                                                serde_json::to_string(&request_body).unwrap_or_default());
                                        }

                                        let response = client.post("https://api.groq.com/openai/v1/chat/completions")
                                            .header("Authorization", format!("Bearer {}", api_key))
                                            .header("Content-Type", "application/json")
                                            .json(&request_body)
                                            .send()
                                            .await;

                                        if debug && response.is_ok() {
                                            println!("Worker {}: Got response status: {}", worker_id, 
                                                response.as_ref().unwrap().status());
                                        }

                                        response
                                    },
                                    "sambanova" => {
                                        let mut request_body = request_json.clone();
                                        request_body.as_object_mut().map(|obj| obj.remove("_headers"));

                                        // Enable streaming by default for SambaNova
                                        if let Some(obj) = request_body.as_object_mut() {
                                            obj.insert("stream".to_string(), serde_json::json!(true));
                                        }

                                        if debug {
                                            println!("Worker {}: Processing SambaNova request", worker_id);
                                            println!("Worker {}: Request body: {}", worker_id, 
                                                serde_json::to_string(&request_body).unwrap_or_default());
                                        }

                                        let response = client.post("https://api.sambanova.ai/v1/chat/completions")
                                            .header("Authorization", format!("Bearer {}", api_key))
                                            .header("Content-Type", "application/json")
                                            .json(&request_body)
                                            .send()
                                            .await;

                                        if debug && response.is_ok() {
                                            println!("Worker {}: Got response status: {}", worker_id, 
                                                response.as_ref().unwrap().status());
                                        }

                                        response
                                    },
                                    _ => {
                                        let client = reqwest::Client::new();
                                        client.get("invalid://url")
                                            .send()
                                            .await
                                    },
                                };

                                let _response: Result<(), reqwest::Error> = match response {
                                    Ok(resp) => {
                                        buffer.clear();
                                        let stream = resp.bytes_stream();
                                        
                                        tokio::pin!(stream);
                                        while let Some(chunk_result) = stream.next().await {
                                            if let Ok(bytes) = chunk_result {
                                                buffer.reserve(bytes.len());
                                                buffer.extend_from_slice(&bytes);
                                                
                                                if let Ok(text) = String::from_utf8(buffer.clone()) {
                                                    if let Ok(parsed) = serde_json::from_str::<Value>(&text) {
                                                        match provider.as_str() {
                                                            "gemini" => {
                                                                if let Some(_content) = parsed.get("candidates") {
                                                                    response_tx.try_send(text).ok();
                                                                    break;
                                                                }
                                                            },
                                                            "openai" => {
                                                                if let Some(choices) = parsed.get("choices") {
                                                                    if let Some(first) = choices.as_array().and_then(|c| c.first()) {
                                                                        if let Some(message) = first.get("message") {
                                                                            if let Some(content) = message.get("content") {
                                                                                response_tx.try_send(content.to_string()).ok();
                                                                                break;
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            },
                                                            _ => {
                                                                response_tx.try_send(text).ok();
                                                                break;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        Ok(())
                                    },
                                    Err(e) if e.is_connect() || e.is_timeout() => {
                                        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
                                        continue;
                                    },
                                    Err(_) => continue,
                                };
                            } else {
                                if debug {
                                    println!("Worker {}: Failed to get API key from headers", worker_id);
                                }
                            }
                        }
                    }

                    {
                        let mut active = active_requests.write().await;
                        *active -= 1;
                    }
                }
            });
        }

        Ok(BhumiCore {
            sender,
            response_receiver,
            runtime: runtime_clone,
            max_concurrent,
            active_requests,
            debug,
            client,
            stream_buffer_size,
            model: model.to_string(),
            use_grounding,
            provider,
        })
    }

    fn completion(&self, model: &str, messages: &PyAny, api_key: &str) -> PyResult<LLMResponse> {
        let (provider, model_name) = match model.split_once('/') {
            Some((p, m)) => (p, m),
            None => (model, model),
        };

        let messages_json: Vec<serde_json::Value> = messages.extract::<Vec<&PyDict>>()?
            .iter()
            .map(|dict| {
                let role = dict.get_item("role")
                    .unwrap()
                    .and_then(|v| v.extract::<String>().ok())
                    .unwrap_or_else(|| "user".to_string());
                
                let content = dict.get_item("content")
                    .unwrap()
                    .and_then(|v| v.extract::<String>().ok())
                    .unwrap_or_default();
                
                serde_json::json!({
                    "role": role,
                    "content": content
                })
            })
            .collect();

        let request = serde_json::json!({
            "_headers": {
                "Authorization": api_key
            },
            "messages": messages_json
        });

        self.submit(request.to_string())?;
        
        let start = std::time::Instant::now();
        while start.elapsed() < std::time::Duration::from_secs(30) {
            if let Some(response) = self.get_response()? {
                match self.provider.as_str() {
                    "gemini" => {
                        if let Ok(gemini_resp) = serde_json::from_str::<GeminiResponse>(&response) {
                            return Ok(LLMResponse {
                                text: gemini_resp.get_text(),
                                raw_response: response,
                            });
                        }
                    },
                    _ => {
                        return Ok(LLMResponse {
                            text: response.clone(),
                            raw_response: response,
                        });
                    }
                }
            }
            std::thread::sleep(std::time::Duration::from_millis(10));
        }

        Err(PyErr::new::<pyo3::exceptions::PyTimeoutError, _>("Request timed out"))
    }

    #[pyo3(name = "_submit")]
    fn submit(&self, request: String) -> PyResult<()> {
        let sender = self.sender.clone();
        self.runtime.block_on(async {
            let sender = sender.lock().await;
            sender.send(request)
                .await
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            Ok(())
        })
    }

    #[pyo3(name = "_get_response")]
    fn get_response(&self) -> PyResult<Option<String>> {
        let receiver = self.response_receiver.clone();
        self.runtime.block_on(async {
            let mut receiver = receiver.lock().await;
            match receiver.try_recv() {
                Ok(response) => Ok(Some(response)),
                Err(_) => {
                    match tokio::time::timeout(
                        tokio::time::Duration::from_millis(10),
                        receiver.recv()
                    ).await {
                        Ok(Some(response)) => Ok(Some(response)),
                        _ => Ok(None),
                    }
                }
            }
        })
    }

    fn is_idle(&self) -> PyResult<bool> {
        self.runtime.block_on(async {
            let active = self.active_requests.read().await;
            Ok(*active == 0)
        })
    }
}

impl LLMResponse {
    fn from_gemini(response: GeminiResponse) -> Self {
        LLMResponse {
            text: response.get_text(),
            raw_response: serde_json::to_string(&response).unwrap_or_default(),
        }
    }

    fn from_openai(response: OpenAIResponse) -> Self {
        LLMResponse {
            text: response.get_text(),
            raw_response: serde_json::to_string(&response).unwrap_or_default(),
        }
    }
}

#[pymodule]
fn bhumi(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<LLMResponse>()?;
    m.add_class::<BhumiCore>()?;
    Ok(())
} 