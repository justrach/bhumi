// use serde::{Deserialize, Serialize};
// use serde_json::{Value, Error};

// // Response types only need Deserialize
// #[derive(Debug, Deserialize)]
// pub struct GeminiResponse {
//     pub candidates: Vec<Candidate>,
//     pub usageMetadata: Option<UsageMetadata>,
//     pub modelVersion: Option<String>,
// }

// #[derive(Debug, Deserialize)]
// pub struct Candidate {
//     pub content: Content,
//     pub finishReason: Option<String>,
//     pub groundingMetadata: Option<GroundingMetadata>,
// }

// // This needs both since it's used in both request and response
// #[derive(Debug, Serialize, Deserialize)]
// pub struct Content {
//     pub parts: Vec<Part>,
//     pub role: Option<String>,
// }

// #[derive(Debug, Serialize, Deserialize)]
// pub struct Part {
//     pub text: String,
// }

// // Rest of response types only need Deserialize
// #[derive(Debug, Deserialize)]
// pub struct GroundingMetadata {
//     pub searchEntryPoint: Option<SearchEntryPoint>,
//     pub groundingChunks: Vec<GroundingChunk>,
//     pub groundingSupports: Vec<GroundingSupport>,
//     pub retrievalMetadata: Value,
//     pub webSearchQueries: Vec<String>,
// }

// #[derive(Debug, Deserialize)]
// pub struct SearchEntryPoint {
//     pub renderedContent: String,
// }

// #[derive(Debug, Deserialize)]
// pub struct GroundingChunk {
//     pub web: WebSource,
// }

// #[derive(Debug, Deserialize)]
// pub struct WebSource {
//     pub uri: String,
//     pub title: String,
// }

// #[derive(Debug, Deserialize)]
// pub struct GroundingSupport {
//     pub segment: TextSegment,
//     pub groundingChunkIndices: Vec<usize>,
//     pub confidenceScores: Vec<f64>,
// }

// #[derive(Debug, Deserialize)]
// pub struct TextSegment {
//     pub startIndex: Option<usize>,
//     pub endIndex: usize,
//     pub text: String,
// }

// #[derive(Debug, Deserialize)]
// pub struct UsageMetadata {
//     pub promptTokenCount: usize,
//     pub candidatesTokenCount: usize,
//     pub totalTokenCount: usize,
//     pub promptTokensDetails: Vec<TokenDetails>,
//     pub candidatesTokensDetails: Vec<TokenDetails>,
// }

// #[derive(Debug, Deserialize)]
// pub struct TokenDetails {
//     pub modality: String,
//     pub tokenCount: usize,
// }

// // Request types only need Serialize
// #[derive(Debug, Serialize)]
// pub struct GeminiRequest {
//     pub contents: Vec<Content>,
//     #[serde(skip_serializing_if = "Option::is_none")]
//     pub tools: Option<Vec<Tool>>,
// }

// #[derive(Debug, Serialize)]
// pub struct Tool {
//     pub google_search: Option<GoogleSearch>,
// }

// #[derive(Debug, Serialize)]
// pub struct GoogleSearch {}

// impl GeminiResponse {
//     pub fn get_text(&self) -> String {
//         self.candidates
//             .first()
//             .and_then(|c| c.content.parts.first())
//             .map(|p| p.text.clone())
//             .unwrap_or_default()
//     }

//     pub fn get_raw(&self) -> String {
//         serde_json::to_string(self).unwrap_or_default()
//     }

//     pub fn get_grounding_chunks(&self) -> Vec<&GroundingChunk> {
//         self.candidates
//             .first()
//             .and_then(|c| c.groundingMetadata.as_ref())
//             .map(|gm| gm.groundingChunks.iter().collect())
//             .unwrap_or_default()
//     }

//     pub fn get_search_queries(&self) -> Vec<&String> {
//         self.candidates
//             .first()
//             .and_then(|c| c.groundingMetadata.as_ref())
//             .map(|gm| gm.webSearchQueries.iter().collect())
//             .unwrap_or_default()
//     }

//     pub fn from_json(json: Value) -> Result<Self, Error> {
//         serde_json::from_value(json)
//     }
// } 