use serde::{Deserialize, Serialize};
use serde_json::{Value, Error};

#[derive(Deserialize, Serialize, Debug)]
pub struct GeminiResponse {
    pub candidates: Vec<Candidate>,
    pub usageMetadata: Option<UsageMetadata>,
    pub modelVersion: Option<String>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct Candidate {
    pub content: Content,
    pub finishReason: Option<String>,
    pub groundingMetadata: Option<GroundingMetadata>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct Content {
    pub parts: Vec<Part>,
    pub role: Option<String>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct Part {
    pub text: String,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct GroundingMetadata {
    pub searchEntryPoint: Option<SearchEntryPoint>,
    pub groundingChunks: Vec<GroundingChunk>,
    pub groundingSupports: Vec<GroundingSupport>,
    pub retrievalMetadata: Value,
    pub webSearchQueries: Vec<String>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct SearchEntryPoint {
    pub renderedContent: String,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct GroundingChunk {
    pub web: WebSource,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct WebSource {
    pub uri: String,
    pub title: String,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct GroundingSupport {
    pub segment: TextSegment,
    pub groundingChunkIndices: Vec<usize>,
    pub confidenceScores: Vec<f64>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct TextSegment {
    pub startIndex: Option<usize>,
    pub endIndex: usize,
    pub text: String,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct UsageMetadata {
    pub promptTokenCount: usize,
    pub candidatesTokenCount: usize,
    pub totalTokenCount: usize,
    pub promptTokensDetails: Vec<TokenDetails>,
    pub candidatesTokensDetails: Vec<TokenDetails>,
}

#[derive(Deserialize, Serialize, Debug)]
pub struct TokenDetails {
    pub modality: String,
    pub tokenCount: usize,
}

// Request structures
#[derive(Serialize)]
pub struct GeminiRequest {
    pub contents: Vec<Content>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<Tool>>,
}

#[derive(Serialize)]
pub struct Tool {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub google_search: Option<GoogleSearch>,
}

#[derive(Serialize)]
pub struct GoogleSearch {}

impl GeminiResponse {
    pub fn get_text(&self) -> String {
        self.candidates
            .first()
            .and_then(|c| c.content.parts.first())
            .map(|p| p.text.clone())
            .unwrap_or_default()
    }

    pub fn get_raw(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    pub fn get_grounding_chunks(&self) -> Vec<&GroundingChunk> {
        self.candidates
            .first()
            .and_then(|c| c.groundingMetadata.as_ref())
            .map(|gm| gm.groundingChunks.iter().collect())
            .unwrap_or_default()
    }

    pub fn get_search_queries(&self) -> Vec<&String> {
        self.candidates
            .first()
            .and_then(|c| c.groundingMetadata.as_ref())
            .map(|gm| gm.webSearchQueries.iter().collect())
            .unwrap_or_default()
    }

    pub fn from_json(json: Value) -> Result<Self, Error> {
        serde_json::from_value(json)
    }
} 