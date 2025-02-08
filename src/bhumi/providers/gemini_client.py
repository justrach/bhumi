from ..base import BaseLLM, LLMConfig
import httpx
from typing import Dict, Any, AsyncIterator, List
import json

class GeminiLLM(BaseLLM):
    """Gemini implementation of BaseLLM"""
    
    def _setup_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._prepare_headers()
        )
    
    def _prepare_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key  # Gemini uses x-goog-api-key
        }
    
    def _prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        # Convert OpenAI-style messages to Gemini format
        contents = []
        for msg in messages:
            if msg["role"] != "system":  # Gemini doesn't use system messages
                contents.append({
                    "parts": [{"text": msg["content"]}],
                    "role": "user" if msg["role"] == "user" else "model"
                })
        
        return {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "topP": kwargs.get("top_p", 0.8),
                "topK": kwargs.get("top_k", 40),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            }
        }
    
    async def _make_request(self, request: Dict[str, Any]) -> httpx.Response:
        url = f"{self.config.base_url}/{self.config.model_name}:generateContent"
        response = await self.client.post(url, json=request)
        response.raise_for_status()
        return response
    
    async def _make_streaming_request(self, request: Dict[str, Any]) -> httpx.Response:
        url = f"{self.config.base_url}/{self.config.model_name}:streamGenerateContent"
        response = await self.client.post(url, json=request)
        response.raise_for_status()
        return response
    
    async def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        data = response.json()
        return {
            "text": data["candidates"][0]["content"]["parts"][0]["text"],
            "raw_response": data
        }
    
    async def _process_stream(self, response: httpx.Response) -> AsyncIterator[str]:
        async for line in response.aiter_bytes():
            try:
                if line.strip():
                    chunk = json.loads(line)
                    if "candidates" in chunk:
                        if text := chunk["candidates"][0]["content"]["parts"][0]["text"]:
                            yield text
            except json.JSONDecodeError:
                if self.config.debug:
                    print(f"Failed to decode chunk: {line}")
                continue 