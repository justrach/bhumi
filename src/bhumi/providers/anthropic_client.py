from ..base import BaseLLM, LLMConfig
import httpx
from typing import Dict, Any, AsyncIterator, List
import json
import asyncio

class AnthropicLLM(BaseLLM):
    """Anthropic implementation of BaseLLM"""
    
    def _setup_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._prepare_headers()
        )
    
    def _prepare_headers(self) -> Dict[str, str]:
        headers = {
            "content-type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }
        if self.config.headers:
            # Don't allow overriding anthropic-version
            headers.update({k:v for k,v in self.config.headers.items() if k != "anthropic-version"})
        return headers
    
    def _prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        # Convert OpenAI-style messages to Anthropic format
        system = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
        messages = [msg for msg in messages if msg["role"] != "system"]
        
        request = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "assistant" if msg["role"] == "assistant" else "user",
                    "content": msg["content"]
                }
                for msg in messages
            ],
            "max_tokens": kwargs.get("max_tokens", 1024)
        }
        
        if system:
            request["system"] = system
            
        # Add Anthropic-specific parameters
        if "temperature" in kwargs:
            request["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            request["top_p"] = kwargs["top_p"]
            
        return request
    
    async def _make_request(self, request: Dict[str, Any]) -> httpx.Response:
        url = f"{self.config.base_url}/messages"
        response = await self.client.post(url, json=request)
        response.raise_for_status()
        return response
    
    async def _make_streaming_request(self, request: Dict[str, Any]) -> httpx.Response:
        request = request.copy()
        request["stream"] = True
        return await self._make_request(request)
    
    async def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        data = response.json()
        return {
            "text": data["content"][0]["text"],
            "raw_response": data
        }
    
    async def _process_stream(self, response: httpx.Response) -> AsyncIterator[str]:
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                event_type = line.removeprefix("event: ").strip()
                continue
                
            if line.startswith("data: "):
                try:
                    data = json.loads(line.removeprefix("data: "))
                    
                    if data["type"] == "content_block_delta":
                        if text := data["delta"].get("text", ""):
                            # Add small delay to make streaming visible
                            await asyncio.sleep(0.05)  # 50ms delay
                            yield text
                            
                except json.JSONDecodeError:
                    if self.config.debug:
                        print(f"Failed to decode chunk: {line}")
                    continue 