use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqResponse {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<GroqChoice>,
    pub usage: GroqUsage,
    pub system_fingerprint: Option<String>,
    pub x_groq: Option<GroqMetadata>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqChoice {
    pub index: i32,
    pub message: GroqMessage,
    pub logprobs: Option<serde_json::Value>,
    pub finish_reason: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqMessage {
    pub role: String,
    pub content: String,
    pub tool_calls: Option<Vec<GroqToolCall>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqToolCall {
    pub id: String,
    pub r#type: String,
    pub function: GroqFunctionCall,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqFunctionCall {
    pub name: String,
    pub arguments: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqUsage {
    pub prompt_tokens: i32,
    pub completion_tokens: i32,
    pub total_tokens: i32,
    pub queue_time: f64,
    pub prompt_time: f64,
    pub completion_time: f64,
    pub total_time: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GroqMetadata {
    pub id: String,
}

// Request structures
#[derive(Debug, Serialize)]
pub struct GroqRequest {
    pub model: String,
    pub messages: Vec<GroqMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_p: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub n: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stop: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_completion_tokens: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub presence_penalty: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub frequency_penalty: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<GroqTool>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_choice: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub seed: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct GroqTool {
    pub r#type: String,
    pub function: GroqFunction,
}

#[derive(Debug, Serialize)]
pub struct GroqFunction {
    pub name: String,
    pub description: Option<String>,
    pub parameters: serde_json::Value,
}

impl GroqResponse {
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