use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize)]
pub struct OpenAIRequest {
    pub model: String,
    pub messages: Vec<Message>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub refusal: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OpenAIResponse {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<Choice>,
    pub usage: Usage,
    pub service_tier: String,
    pub system_fingerprint: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Choice {
    pub index: i32,
    pub message: Message,
    pub logprobs: Option<serde_json::Value>,
    pub finish_reason: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Usage {
    pub prompt_tokens: i32,
    pub completion_tokens: i32,
    pub total_tokens: i32,
    pub prompt_tokens_details: TokenDetails,
    pub completion_tokens_details: CompletionTokenDetails,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TokenDetails {
    pub cached_tokens: i32,
    pub audio_tokens: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CompletionTokenDetails {
    pub reasoning_tokens: i32,
    pub audio_tokens: i32,
    pub accepted_prediction_tokens: i32,
    pub rejected_prediction_tokens: i32,
}

impl OpenAIResponse {
    pub fn get_text(&self) -> String {
        self.choices
            .first()
            .map(|c| c.message.content.clone())
            .unwrap_or_default()
    }

    pub fn from_json(json: serde_json::Value) -> Result<Self, serde_json::Error> {
        serde_json::from_value(json)
    }
} 