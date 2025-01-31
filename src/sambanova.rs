use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct SambanovaResponse {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<SambanovaChoice>,
    pub system_fingerprint: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SambanovaChoice {
    pub index: i32,
    pub delta: SambanovaDelta,
    pub finish_reason: Option<String>,
    pub logprobs: Option<serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SambanovaDelta {
    pub content: String,
    pub role: Option<String>,
}

// Request structures
#[derive(Debug, Serialize)]
pub struct SambanovaRequest {
    pub model: String,
    pub messages: Vec<SambanovaMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct SambanovaMessage {
    pub role: String,
    pub content: String,
}

impl SambanovaResponse {
    pub fn get_text(&self) -> String {
        self.choices
            .first()
            .map(|c| c.delta.content.clone())
            .unwrap_or_default()
    }

    pub fn from_json(json: serde_json::Value) -> Result<Self, serde_json::Error> {
        serde_json::from_value(json)
    }
} 