use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::sync::Arc;
use tokio::sync::mpsc;
use serde_json::Value;
use futures_util::StreamExt;
use std::collections::VecDeque;
use std::sync::Mutex;
use tokio::time::sleep;
use std::time::Duration;
use std::future::Future;

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
    stream_chunks: Arc<Mutex<VecDeque<String>>>,
    base_url: String,  // Add base URL field
}

#[pymethods]
impl BhumiCore {
    #[new]
    #[pyo3(signature = (
        max_concurrent,
        provider="",  // Empty string by default
        model="",
        use_grounding=false,
        debug=false,
        stream_buffer_size=1000,
        base_url=None
    ))]
    fn new(
        max_concurrent: usize,
        provider: &str,
        model: &str,
        use_grounding: bool,
        debug: bool,
        stream_buffer_size: usize,
        base_url: Option<&str>,
    ) -> PyResult<Self> {
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

        let stream_chunks = Arc::new(Mutex::new(VecDeque::new()));

        let base_url = match base_url {
            Some(url) => url.to_string(),
            None => "".to_string(),  // Empty string by default
        };

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
            let stream_chunks = stream_chunks.clone();
            let base_url = base_url.clone();
            
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
                                let response = if provider == "openai" {
                                    // OpenAI specific handling
                                    let mut request_body = request_json.clone();
                                    request_body.as_object_mut().map(|obj| obj.remove("_headers"));

                                    if debug {
                                        println!("Worker {}: Processing OpenAI request", worker_id);
                                    }

                                    let url = format!("{}/chat/completions", base_url);

                                    if debug {
                                        println!("Worker {}: Sending request to API: {}", worker_id, url);
                                    }

                                    process_request(&client, &url, &request_body, api_key, debug).await
                                } else {
                                    // Generic OpenAI-compatible API handler
                                    let mut request_body = request_json.clone();
                                    request_body.as_object_mut().map(|obj| obj.remove("_headers"));

                                    if debug {
                                        println!("Worker {}: Processing request", worker_id);
                                    }

                                    let url = format!("{}/chat/completions", base_url);

                                    if debug {
                                        println!("Worker {}: Sending request to API: {}", worker_id, url);
                                    }

                                    process_request(&client, &url, &request_body, api_key, debug).await
                                };

                                let _response: Result<(), reqwest::Error> = match response {
                                    Ok(resp) => {
                                        buffer.clear();
                                        let stream = resp.bytes_stream();
                                        
                                        tokio::pin!(stream);
                                        while let Some(chunk_result) = stream.next().await {
                                            if let Ok(bytes) = chunk_result {
                                                if request_json.get("stream").and_then(|s| s.as_bool()).unwrap_or(false) {
                                                    if let Ok(text) = String::from_utf8(bytes.to_vec()) {
                                                        for line in text.lines() {
                                                            if !line.is_empty() {
                                                                if line == "data: [DONE]" {
                                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                                    chunks.push_back("[DONE]".to_string());
                                                                    break;  // Important: break the streaming loop
                                                                } else if line.starts_with("data: ") {
                                                                    if let Ok(chunk_json) = serde_json::from_str::<Value>(
                                                                        line.trim_start_matches("data: ")
                                                                    ) {
                                                                        // Extract just the content from the delta
                                                                        if let Some(content) = chunk_json
                                                                            .get("choices")
                                                                            .and_then(|c| c.get(0))
                                                                            .and_then(|c| c.get("delta"))
                                                                            .and_then(|d| d.get("content"))
                                                                            .and_then(|c| c.as_str()) 
                                                                        {
                                                                            let mut chunks = stream_chunks.lock().unwrap();
                                                                            chunks.push_back(content.to_string());
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                } else {
                                                    // Non-streaming response handling
                                                    buffer.extend_from_slice(&bytes);
                                                    if let Ok(text) = String::from_utf8(buffer.clone()) {
                                                        if serde_json::from_str::<Value>(&text).is_ok() {
                                                            response_tx.try_send(text).ok();
                                                            break;
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
            stream_chunks,
            base_url,
        })
    }

    fn completion(&self, model: &str, messages: &PyAny, api_key: &str) -> PyResult<LLMResponse> {
        let (_provider, _model_name) = match model.split_once('/') {
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

    fn _get_stream_chunk(&self) -> Option<String> {
        let mut chunks = self.stream_chunks.lock().unwrap();
        chunks.pop_front()
    }
    
    fn _process_stream_response(&self, response: String) {
        // Split response into SSE chunks
        for line in response.lines() {
            if line.starts_with("data: ") {
                let chunk = line.trim_start_matches("data: ").to_string();
                let mut chunks = self.stream_chunks.lock().unwrap();
                chunks.push_back(chunk);
            }
        }
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

// Add a retry helper function
async fn retry_with_backoff<F, Fut, T, E>(
    mut f: F,
    max_retries: u32,
    initial_delay_ms: u64,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
{
    let mut retries = 0;
    let mut delay = initial_delay_ms;

    loop {
        match f().await {
            Ok(result) => return Ok(result),
            Err(e) => {
                if retries >= max_retries {
                    return Err(e);
                }
                retries += 1;
                sleep(Duration::from_millis(delay)).await;
                delay *= 2; // Exponential backoff
            }
        }
    }
}

// Now update the actual request sending to use retry
async fn process_request(
    client: &reqwest::Client,
    url: &str,
    request_json: &Value,
    api_key: &str,
    debug: bool,
) -> Result<reqwest::Response, reqwest::Error> {
    retry_with_backoff(
        || async {
            client
                .post(url)
                .header("Authorization", format!("Bearer {}", api_key))
                .header("Content-Type", "application/json")
                .json(request_json)
                .send()
                .await
        },
        3, // max retries
        100, // initial delay in ms
    )
    .await
}

#[pymodule]
fn bhumi(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<LLMResponse>()?;
    m.add_class::<BhumiCore>()?;
    Ok(())
} 