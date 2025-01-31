use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct AnthropicContent {
    #[serde(rename = "type")]
    pub content_type: String,
    pub text: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AnthropicUsage {
    pub input_tokens: u32,
    pub output_tokens: u32,
    #[serde(default)]
    pub cache_creation_input_tokens: u32,
    #[serde(default)]
    pub cache_read_input_tokens: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AnthropicResponse {
    pub id: String,
    #[serde(rename = "type")]
    pub response_type: String,
    pub role: String,
    pub model: String,
    pub content: Vec<AnthropicContent>,
    pub stop_reason: String,
    #[serde(default)]
    pub stop_sequence: Option<String>,
    pub usage: AnthropicUsage,
}

impl AnthropicResponse {
    // Helper method to get the text content
    pub fn get_text(&self) -> String {
        self.content
            .iter()
            .filter(|c| c.content_type == "text")
            .map(|c| c.text.clone())
            .collect::<Vec<String>>()
            .join("\n")
    }
} 