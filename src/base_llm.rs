use serde_json::Value;
use std::sync::Arc;
use tokio::sync::mpsc;
use futures_util::StreamExt;
use std::collections::VecDeque;
use std::sync::Mutex;

pub struct BaseLLMConfig {
    pub api_base: String,
    pub api_key_header: String,  // e.g. "Authorization: Bearer" or "x-api-key"
    pub model_path: String,      // e.g. "/v1/chat/completions" or "/generate"
    pub stream_marker: String,   // e.g. "data: [DONE]" or "[DONE]"
    pub stream_field_path: Vec<String>, // e.g. ["choices", 0, "delta", "content"]
    pub content_field_path: Vec<String>, // e.g. ["choices", 0, "message", "content"]
}

impl Default for BaseLLMConfig {
    fn default() -> Self {
        Self {
            api_base: "https://api.openai.com".to_string(),
            api_key_header: "Authorization: Bearer".to_string(),
            model_path: "/v1/chat/completions".to_string(),
            stream_marker: "data: [DONE]".to_string(),
            stream_field_path: vec!["choices".to_string(), "0".to_string(), "delta".to_string(), "content".to_string()],
            content_field_path: vec!["choices".to_string(), "0".to_string(), "message".to_string(), "content".to_string()],
        }
    }
}

pub struct BaseLLM {
    config: BaseLLMConfig,
    client: Arc<reqwest::Client>,
    stream_chunks: Arc<Mutex<VecDeque<String>>>,
}

impl BaseLLM {
    pub fn new(config: BaseLLMConfig, client: Arc<reqwest::Client>, stream_chunks: Arc<Mutex<VecDeque<String>>>) -> Self {
        Self {
            config,
            client,
            stream_chunks,
        }
    }

    pub async fn process_request(
        &self,
        request_json: &Value,
        api_key: &str,
        debug: bool,
        worker_id: usize,
    ) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.config.api_base, self.config.model_path);
        
        if debug {
            println!("Worker {}: Sending request to {}", worker_id, url);
        }

        self.client
            .post(&url)
            .header(
                self.config.api_key_header.split_once(": ").unwrap().0,
                format!("{} {}", self.config.api_key_header.split_once(": ").unwrap().1, api_key)
            )
            .header("Content-Type", "application/json")
            .header("Accept", "text/event-stream")
            .json(&request_json)
            .send()
            .await
    }

    pub fn process_stream_chunk(&self, line: &str) -> Option<String> {
        if line == self.config.stream_marker {
            return Some("[DONE]".to_string());
        }

        if line.starts_with("data: ") {
            if let Ok(chunk_json) = serde_json::from_str::<Value>(
                line.trim_start_matches("data: ")
            ) {
                // Navigate through the JSON using field path
                let mut current = &chunk_json;
                for field in &self.config.stream_field_path {
                    current = match field.parse::<usize>() {
                        Ok(idx) => current.get(idx)?,
                        Err(_) => current.get(field)?,
                    };
                }
                
                if let Some(content) = current.as_str() {
                    return Some(content.to_string());
                }
            }
        }
        None
    }

    pub fn process_completion_response(&self, response: &str) -> Option<String> {
        if let Ok(response_json) = serde_json::from_str::<Value>(response) {
            // Navigate through the JSON using field path
            let mut current = &response_json;
            for field in &self.config.content_field_path {
                current = match field.parse::<usize>() {
                    Ok(idx) => current.get(idx)?,
                    Err(_) => current.get(field)?,
                };
            }
            
            if let Some(content) = current.as_str() {
                return Some(content.to_string());
            }
        }
        None
    }

    pub fn queue_chunk(&self, chunk: String) {
        let mut chunks = self.stream_chunks.lock().unwrap();
        chunks.push_back(chunk);
    }
} 