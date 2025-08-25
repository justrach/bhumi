//! Bhumi is a high-performance LLM client library with batching capabilities.
//! 
//! # Features
//! 
//! - Async/await support
//! - Batch processing
//! - Python bindings
//! - Multiple LLM provider support
//! 
//! # Example
//! 
//! ```rust
//! use bhumi::Client;
//! 
//! #[tokio::main]
//! async fn main() {
//!     // Example code here
//! }
//! ```

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
use reqwest::header::{HeaderMap, HeaderValue, ACCEPT};
use bytes;

mod anthropic;
mod openai;

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
    debug_debug: bool,
    client: Arc<reqwest::Client>,
    stream_buffer_size: usize,
    model: String,
    use_grounding: bool,
    provider: String,  // "anthropic", "gemini", "openai", "groq", or "sambanova"
    stream_chunks: Arc<Mutex<VecDeque<String>>>,
    base_url: Option<String>,  // Change to Option<String>
    max_tokens: Option<i32>,  // Add max_tokens field
    buffer_size: usize,
}

#[pymethods]
impl BhumiCore {
    #[new]
    #[pyo3(signature = (
        max_concurrent,
        provider="",
        model="",
        use_grounding=false,
        debug=false,
        debug_debug=false,
        stream_buffer_size=1000,
        base_url=None,
        buffer_size=131072  // Back to 128KB for optimal performance
    ))]
    fn new(
        max_concurrent: usize,
        provider: &str,
        model: &str,
        use_grounding: bool,
        debug: bool,
        debug_debug: bool,
        stream_buffer_size: usize,
        base_url: Option<&str>,
        buffer_size: usize,
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

        // Build HTTP client with optional HTTP/1.1 fallback and sensible timeouts
        let mut client_builder = reqwest::Client::builder()
            .pool_max_idle_per_host(max_concurrent * 2)
            .tcp_keepalive(Some(std::time::Duration::from_secs(30)))
            .tcp_nodelay(true)
            .pool_idle_timeout(Some(std::time::Duration::from_secs(60)))
            .http2_keep_alive_interval(std::time::Duration::from_secs(20))
            .http2_keep_alive_timeout(std::time::Duration::from_secs(30))
            .http2_adaptive_window(true)
            .pool_max_idle_per_host(100)
            .connect_timeout(std::time::Duration::from_secs(10));
        if std::env::var("BHUMI_HTTP1").ok().as_deref() == Some("1") {
            client_builder = client_builder.http1_only();
        }
        let client = Arc::new(client_builder.build().unwrap());

        let stream_chunks = Arc::new(Mutex::new(VecDeque::new()));

        // Get base URL based on provider if not explicitly provided
        let base_url = match base_url {
            Some(url) => url.to_string(),
            None => {
                // Extract provider from model string if present
                let provider_str = if model.contains('/') {
                    model.split('/').next().unwrap_or("")
                } else {
                    &provider  // Borrow the String to get &str
                };
                
                match provider_str {
                    "openai" => "https://api.openai.com/v1".to_string(),
                    "anthropic" => "https://api.anthropic.com/v1".to_string(),
                    "gemini" => "https://generativelanguage.googleapis.com/v1beta/openai".to_string(),
                    _ => "".to_string()
                }
            }
        };

        // Spawn workers
        for worker_id in 0..max_concurrent {
            let request_rx = request_rx.clone();
            let response_tx = response_tx.clone();
            let active_requests = active_requests.clone();
            let client = client.clone();
            let debug = debug;
            let debug_debug = debug_debug;
            let provider = provider.clone();
            let model = model.to_string();
            let use_grounding = use_grounding;
            let stream_chunks = stream_chunks.clone();
            let base_url = base_url.clone();
            
            runtime.spawn(async move {
                if debug {
                    println!("Starting worker {}", worker_id);
                }
                let mut buffer: Vec<u8> = Vec::with_capacity(32768);
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

                        let _model = model.to_string();
                        let _use_grounding = use_grounding;

                        if let Ok(request_json) = serde_json::from_str::<Value>(&request_str) {
                            let api_key = request_json
                                .get("_headers")
                                .and_then(|h| h.as_object())
                                .and_then(|h| h.get("Authorization").or_else(|| h.get("x-api-key")))  // Try both header types
                                .and_then(|k| k.as_str());

                            if let Some(api_key) = api_key {
                                if debug {
                                    println!("Worker {}: Got API key", worker_id);
                                }
                                
                                let response = match provider.as_str() {
                                    _ => {
                                        // Allow Python layer to override endpoint (e.g., images API)
                                        let endpoint_override = request_json
                                            .get("_endpoint")
                                            .and_then(|v| v.as_str());

                                        if debug_debug { eprintln!("[bhumi][pre1] Worker {}: computing URL ...", worker_id); }
                                        let url = if let Some(ep) = endpoint_override {
                                            ep.to_string()
                                        } else if provider == "anthropic" {
                                            format!("{}/messages", base_url)
                                        } else {
                                            format!("{}/chat/completions", base_url)
                                        };
                                        if debug_debug { eprintln!("[bhumi][pre2] Worker {}: URL computed: {}", worker_id, url); }

                                        // Determine if streaming request early for reuse
                                        let is_streaming_req = request_json
                                            .get("stream")
                                            .and_then(|s| s.as_bool())
                                            .unwrap_or(false);

                                        // Set up headers based on provider
                                        if debug_debug { eprintln!("[bhumi][pre3] Worker {}: preparing headers ...", worker_id); }
                                        let mut headers = HeaderMap::new();
                                        if provider == "anthropic" {
                                            headers.insert(
                                                "x-api-key",
                                                HeaderValue::from_str(api_key).unwrap()
                                            );
                                            headers.insert(
                                                "anthropic-version",
                                                HeaderValue::from_str("2023-06-01").unwrap()
                                            );
                                        } else {
                                            // For OpenAI, Groq, Gemini (OpenAI-compatible) etc.
                                            if debug_debug { eprintln!("[bhumi][pre4] Worker {}: inserting Authorization header ...", worker_id); }
                                            headers.insert(
                                                reqwest::header::AUTHORIZATION,
                                                HeaderValue::from_str(api_key).unwrap()
                                            );
                                        }
                                        headers.insert(
                                            reqwest::header::CONTENT_TYPE,
                                            HeaderValue::from_str("application/json").unwrap()
                                        );

                                        // If streaming, explicitly accept event stream
                                        if is_streaming_req {
                                            headers.insert(ACCEPT, HeaderValue::from_static("text/event-stream"));
                                        }

                                        if debug_debug { eprintln!("[bhumi][pre5] Worker {}: headers ready; cloning body ...", worker_id); }
                                        // Remove _headers from request before sending
                                        let mut request_body = request_json.clone();
                                        if debug_debug { eprintln!("[bhumi][pre6] Worker {}: body cloned; sanitizing ...", worker_id); }
                                        request_body.as_object_mut().map(|obj| {
                                            // Remove internal-only fields
                                            obj.remove("_headers");
                                            obj.remove("_endpoint");
                                            // Remove fields known to cause issues for some providers
                                            obj.remove("strict");

                                            // Keep max_tokens if it exists and is not null
                                            if let Some(max_tokens) = obj.get("max_tokens") {
                                                if !max_tokens.is_null() {
                                                    obj.insert("max_tokens".to_string(), max_tokens.clone());
                                                }
                                            }
                                        });

                                        if debug_debug { eprintln!("[bhumi][pre7] Worker {}: body sanitized", worker_id); }
                                        // Summarize sanitized request to help diagnose 4xx without exposing secrets (very verbose)
                                        if debug_debug {
                                            let model = request_body
                                                .get("model")
                                                .and_then(|v| v.as_str())
                                                .unwrap_or("");
                                            let msg_count = request_body
                                                .get("messages")
                                                .and_then(|m| m.as_array())
                                                .map(|a| a.len())
                                                .unwrap_or(0);
                                            let tools_len_dbg = request_body
                                                .get("tools")
                                                .and_then(|t| t.as_array())
                                                .map(|a| a.len())
                                                .unwrap_or(0);
                                            let max_tok = request_body
                                                .get("max_tokens")
                                                .and_then(|v| v.as_i64())
                                                .unwrap_or(-1);
                                            eprintln!(
                                                "[bhumi][pre7.1] Worker {}: model={} messages={} tools={} max_tokens={} stream={}",
                                                worker_id, model, msg_count, tools_len_dbg, max_tok, is_streaming_req
                                            );
                                        }
                                        // Extra debug before send to catch stalls (avoid serializing whole body)
                                        if debug_debug {
                                            let tools_len = request_body
                                                .get("tools")
                                                .and_then(|t| t.as_array())
                                                .map(|a| a.len())
                                                .unwrap_or(0);
                                            eprintln!(
                                                "[bhumi][pre8] Worker {}: Sending request url={} stream={} tools={}",
                                                worker_id, url, is_streaming_req, tools_len
                                            );
                                        }

                                        // Send with a timeout guard to detect handshake stalls
                                        if debug_debug { eprintln!("[bhumi][pre9] Worker {}: issuing POST ...", worker_id); }
                                        let send_fut = client
                                            .post(&url)
                                            .headers(headers)
                                            .json(&request_body)
                                            .send();
                                        if debug_debug { eprintln!("[bhumi][pre10] Worker {}: awaiting send ...", worker_id); }
                                        match tokio::time::timeout(std::time::Duration::from_secs(15), send_fut).await {
                                            Ok(resp) => resp,
                                            Err(_) => {
                                                if debug {
                                                    println!(
                                                        "Worker {}: HTTP send timeout after 15s for url={}",
                                                        worker_id, url
                                                    );
                                                }
                                                // Surface as error to Python so callers don't hang
                                                if is_streaming_req {
                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                    chunks.push_back("{\"error\":\"timeout during send\"}".to_string());
                                                    chunks.push_back("[DONE]".to_string());
                                                } else {
                                                    let _ = response_tx.try_send("{\"error\":\"timeout during send\"}".to_string());
                                                }
                                                // Decrement active and continue to next request
                                                {
                                                    let mut active = active_requests.write().await;
                                                    *active -= 1;
                                                }
                                                continue;
                                            }
                                        }
                                    }
                                };

                                let _response: Result<(), reqwest::Error> = match response {
                                    Ok(resp) => {
                                        // Capture status first (resp.text() consumes resp)
                                        let status = resp.status();
                                        // Log HTTP status in debug mode
                                        if debug {
                                            println!(
                                                "Worker {}: HTTP status {}",
                                                worker_id,
                                                status
                                            );
                                        }

                                        // If non-success, forward body immediately and terminate stream
                                        if !status.is_success() {
                                            match resp.text().await {
                                                Ok(body) => {
                                                    if !body.is_empty() {
                                                        let mut chunks = stream_chunks.lock().unwrap();
                                                        chunks.push_back(body);
                                                    } else {
                                                        let mut chunks = stream_chunks.lock().unwrap();
                                                        chunks.push_back(format!("{{\"error\":\"HTTP {}\"}}", status));
                                                    }
                                                }
                                                Err(_) => {
                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                    chunks.push_back(format!("{{\"error\":\"HTTP {} (no body)\"}}", status));
                                                }
                                            }
                                            let mut chunks = stream_chunks.lock().unwrap();
                                            chunks.push_back("[DONE]".to_string());
                                        } else if request_json.get("stream").and_then(|s| s.as_bool()).unwrap_or(false) {
                                            let stream = resp.bytes_stream();
                                            tokio::pin!(stream);
                                            let mut saw_done = false;
                                            // Buffer for incomplete SSE lines spanning multiple chunks
                                            let mut sse_buffer = String::new();
                                            // Accumulator for multi-line SSE data payloads per event
                                            let mut event_data = String::new();
                                            // Track current SSE event type (e.g., content_block_delta)
                                            let mut current_event: Option<String> = None;
                                            // Track if we enqueued any payload to Python side
                                            let mut enqueued_any = false;
                                            // Accumulate raw body for non-SSE fallback (providers that ignore SSE)
                                            let mut raw_body = String::new();

                                            // Read stream with idle timeout to prevent hangs
                                            loop {
                                                let next_item = tokio::time::timeout(
                                                    std::time::Duration::from_secs(30),
                                                    stream.next()
                                                ).await;
                                                match next_item {
                                                    Ok(Some(chunk_result)) => {
                                                        if let Ok(bytes) = chunk_result {
                                                    if let Ok(text) = String::from_utf8(bytes.to_vec()) {
                                                        // Append to buffer and process complete lines
                                                        sse_buffer.push_str(&text);
                                                        // Also accumulate raw body to support non-SSE fallback
                                                        raw_body.push_str(&text);

                                                        loop {
                                                            // Find next newline (handle both \n and \r\n by trimming CR later)
                                                            if let Some(pos) = sse_buffer.find('\n') {
                                                                let mut line = sse_buffer[..pos].to_string();
                                                                // Drain processed part including the newline
                                                                sse_buffer.drain(..=pos);
                                                                // Trim a trailing CR if present (\r\n)
                                                                if line.ends_with('\r') {
                                                                    line.pop();
                                                                }
                                                                // SSE event delimiter: empty line flushes accumulated data
                                                                if line.is_empty() {
                                                                    if !event_data.is_empty() {
                                                                        let payload = event_data.trim_end_matches('\n').to_string();
                                                                        if provider == "anthropic" {
                                                                            if let Some(ev) = current_event.as_deref() {
                                                                                match ev {
                                                                                    // Forward only relevant Anthropic events to Python
                                                                                    "content_block_delta" | "message_delta" | "content_block_stop" | "message_stop" => {
                                                                                        // Ensure payload is valid JSON; if concatenated, split and push only valid JSON lines
                                                                                        if serde_json::from_str::<Value>(&payload).is_ok() {
                                                                                            let mut chunks = stream_chunks.lock().unwrap();
                                                                                            chunks.push_back(payload);
                                                                                            enqueued_any = true;
                                                                                        } else {
                                                                                            for line_payload in payload.lines() {
                                                                                                if serde_json::from_str::<Value>(line_payload).is_ok() {
                                                                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                                                                    chunks.push_back(line_payload.to_string());
                                                                                                    enqueued_any = true;
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                    _ => { /* ignore other events like message_start */ }
                                                                                }
                                                                            }
                                                                        } else {
                                                                            if payload == "[DONE]" {
                                                                                let mut chunks = stream_chunks.lock().unwrap();
                                                                                chunks.push_back("[DONE]".to_string());
                                                                                saw_done = true;
                                                                                // Break inner loop; outer loop will observe saw_done
                                                                                break;
                                                                            } else if !payload.is_empty() {
                                                                                let mut chunks = stream_chunks.lock().unwrap();
                                                                                chunks.push_back(payload);
                                                                                enqueued_any = true;
                                                                            }
                                                                        }
                                                                        event_data.clear();
                                                                    }
                                                                    continue;
                                                                }

                                                                // If a new event header starts and we have pending data, flush previous event first
                                                                if line.starts_with("event:") {
                                                                    if !event_data.is_empty() {
                                                                        let payload = event_data.trim_end_matches('\n').to_string();
                                                                        if provider == "anthropic" {
                                                                            if let Some(ev) = current_event.as_deref() {
                                                                                match ev {
                                                                                    "content_block_delta" | "message_delta" | "content_block_stop" | "message_stop" => {
                                                                                        if serde_json::from_str::<Value>(&payload).is_ok() {
                                                                                            let mut chunks = stream_chunks.lock().unwrap();
                                                                                            chunks.push_back(payload);
                                                                                        } else {
                                                                                            for line_payload in payload.lines() {
                                                                                                if serde_json::from_str::<Value>(line_payload).is_ok() {
                                                                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                                                                    chunks.push_back(line_payload.to_string());
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                    _ => { /* ignore */ }
                                                                                }
                                                                            }
                                                                        } else {
                                                                            if payload == "[DONE]" {
                                                                                let mut chunks = stream_chunks.lock().unwrap();
                                                                                chunks.push_back("[DONE]".to_string());
                                                                                saw_done = true;
                                                                                break;
                                                                            } else if !payload.is_empty() {
                                                                                let mut chunks = stream_chunks.lock().unwrap();
                                                                                chunks.push_back(payload);
                                                                                enqueued_any = true;
                                                                            }
                                                                        }
                                                                        event_data.clear();
                                                                    }
                                                                    // Update current event; do not enqueue the event header itself
                                                                    let ev = line.trim_start_matches("event:").trim();
                                                                    current_event = if ev.is_empty() { None } else { Some(ev.to_string()) };
                                                                    continue;
                                                                }

                                                                // Accumulate only data lines; ignore other SSE fields (id:, retry:) and comments
                                                                if line.starts_with("data: ") {
                                                                    let data_part = line.trim_start_matches("data: ");
                                                                    event_data.push_str(data_part);
                                                                    event_data.push('\n');
                                                                } else {
                                                                    // Ignore non-data lines for robustness
                                                                    continue;
                                                                }
                                                            } else {
                                                                // No complete line yet; wait for more bytes
                                                                break;
                                                            }
                                                        }

                                                        // If we saw [DONE], stop reading further
                                                        if saw_done {
                                                            break;
                                                        }
                                                    }
                                                        }
                                                    }
                                                    Ok(None) => break,
                                                    Err(_) => {
                                                        if debug {
                                                            println!("Worker {}: stream idle timeout after 30s", worker_id);
                                                        }
                                                        break;
                                                    }
                                                }
                                            }
                                            // Flush any pending event data at end of stream
                                            if !event_data.is_empty() && !saw_done {
                                                let payload = event_data.trim_end_matches('\n').to_string();
                                                if provider == "anthropic" {
                                                    if let Some(ev) = current_event.as_deref() {
                                                        match ev {
                                                            "content_block_delta" | "message_delta" | "content_block_stop" | "message_stop" => {
                                                                if serde_json::from_str::<Value>(&payload).is_ok() {
                                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                                    chunks.push_back(payload);
                                                                    enqueued_any = true;
                                                                } else {
                                                                    for line_payload in payload.lines() {
                                                                        if serde_json::from_str::<Value>(line_payload).is_ok() {
                                                                            let mut chunks = stream_chunks.lock().unwrap();
                                                                            chunks.push_back(line_payload.to_string());
                                                                            enqueued_any = true;
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            _ => {}
                                                        }
                                                    }
                                                } else if !payload.is_empty() {
                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                    chunks.push_back(payload);
                                                    enqueued_any = true;
                                                }
                                            }
                                            // Ensure the Python reader will terminate even if provider omitted [DONE]
                                            if !saw_done {
                                                // Fallback: if no SSE payloads were enqueued but we have a body, forward it once
                                                if !enqueued_any && !raw_body.is_empty() {
                                                    let mut chunks = stream_chunks.lock().unwrap();
                                                    chunks.push_back(raw_body.clone());
                                                    enqueued_any = true;
                                                }
                                                let mut chunks = stream_chunks.lock().unwrap();
                                                chunks.push_back("[DONE]".to_string());
                                            }
                                        } else {
                                            // For non-streaming responses, buffer the entire response
                                            let mut buffer = Vec::with_capacity(32768);
                                            let stream = resp.bytes_stream();
                                            tokio::pin!(stream);
                                            
                                            while let Some(chunk_result) = stream.next().await {
                                                if let Ok(bytes) = chunk_result {
                                                    buffer.extend_from_slice(&bytes);
                                                }
                                            }
                                            
                                            if let Ok(text) = String::from_utf8(buffer) {
                                                if serde_json::from_str::<Value>(&text).is_ok() {
                                                    response_tx.try_send(text).ok();
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
                                if debug_debug {
                                    println!("Worker {}: Request JSON: {:?}", worker_id, request_json);
                                    println!("Worker {}: Headers: {:?}", worker_id, request_json.get("_headers"));
                                }
                                println!("Worker {}: Failed to get API key from headers", worker_id);
                            }
                        } else {
                            if debug {
                                println!("Worker {}: Failed to parse request: {}", worker_id, request_str);
                            }
                        }
                        {
                            let mut active = active_requests.write().await;
                            *active -= 1;
                        }
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
            debug_debug,
            client,
            stream_buffer_size,
            model: model.to_string(),
            use_grounding,
            provider,
            stream_chunks,
            base_url: Some(base_url),  // Store as Option
            max_tokens: None,  // Initialize as None
            buffer_size,
        })
    }

    fn completion(&self, model: &str, messages: &PyAny, api_key: &str) -> PyResult<LLMResponse> {
        let (provider, _model_name) = match model.split_once('/') {
            Some((p, m)) => (p, m),
            None => (model, model),
        };

        // Get base URL from provider if not set
        let _base_url = self.base_url.as_ref().map(|url| url.as_str()).unwrap_or_else(|| {
            match provider {
                "openai" => "https://api.openai.com/v1",
                "anthropic" => "https://api.anthropic.com/v1",
                "gemini" => "https://generativelanguage.googleapis.com/v1beta/openai",
                _ => ""
            }
        });

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
            "model": model,
            "messages": messages_json,
            "stream": false,
            "max_tokens": self.max_tokens  // Use the struct field instead of config
        });

        self.submit(request.to_string())?;
        
        let start = std::time::Instant::now();
        while start.elapsed() < std::time::Duration::from_secs(30) {
            if let Some(response) = self.get_response()? {
                return Ok(LLMResponse {
                    text: response.clone(),
                    raw_response: response,
                });
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

    // Make extract_text accessible from Python
    #[pyo3(name = "_extract_text_rust")]
    fn py_extract_text(&self, response: String) -> PyResult<String> {
        let parsed: Value = serde_json::from_str(&response)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        let text = match self.provider.as_str() {
            "openai" | "groq" | "gemini" => parsed["choices"][0]["message"]["content"]
                .as_str()
                .map(|s| s.to_string()),
            "anthropic" => parsed["content"][0]["text"]
                .as_str()
                .map(|s| s.to_string()),
            _ => None
        };

        Ok(text.unwrap_or(response))
    }
}

impl LLMResponse {
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
    _debug: bool,
) -> Result<reqwest::Response, reqwest::Error> {
    if url.is_empty() {
        // Create an error by making a request to an invalid URL and wrap in Err
        return Err(reqwest::get("http://invalid-url")
            .await
            .expect_err("Expected error for invalid URL"));
    }

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
        3,
        100,
    )
    .await
}

async fn process_response(
    mut stream: impl futures_util::Stream<Item = Result<bytes::Bytes, reqwest::Error>> + Unpin,
    response_tx: mpsc::Sender<String>,
    buffer_size: usize,
) {
    let mut buffer: Vec<u8> = Vec::with_capacity(buffer_size);
    let mut chunk_sizes = Vec::new();  // Track chunk sizes
    
    while let Some(chunk_result) = stream.next().await {
        if let Ok(bytes) = chunk_result {
            chunk_sizes.push(bytes.len());  // Record chunk size
            buffer.extend_from_slice(&bytes);
            
            if buffer.len() >= buffer_size {
                if let Ok(text) = String::from_utf8(buffer.clone()) {
                    // Send chunk statistics along with the text
                    let stats = serde_json::json!({
                        "text": text,
                        "chunk_sizes": chunk_sizes
                    }).to_string();
                    // Send response without debug output
                    let _ = response_tx.try_send(stats.to_string()).ok();
                }
                buffer.clear();
                chunk_sizes.clear();
            }
        }
    }
    
    if !buffer.is_empty() {
        if let Ok(text) = String::from_utf8(buffer) {
            let stats = serde_json::json!({
                "text": text,
                "chunk_sizes": chunk_sizes
            });
            // Send final response without debug output
            let _ = response_tx.try_send(stats.to_string()).ok();
        }
    }
}

#[pymodule]
fn bhumi(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<LLMResponse>()?;
    m.add_class::<BhumiCore>()?;
    Ok(())
} 