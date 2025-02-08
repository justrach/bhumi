from ..base import BaseLLM, LLMConfig
import httpx
from typing import Dict, Any, AsyncIterator, List
import json
import asyncio

class OpenAILLM(BaseLLM):
    """OpenAI implementation of BaseLLM"""
    
    def _setup_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._prepare_headers()
        )
    
    def _prepare_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.headers:
            headers.update(self.config.headers)
        return headers
    
    def _prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        request = {
            "model": self.config.model_name,
            "messages": messages
        }
        
        # Add OpenAI-specific parameters
        if "temperature" in kwargs:
            request["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            request["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            request["top_p"] = kwargs["top_p"]
        if "presence_penalty" in kwargs:
            request["presence_penalty"] = kwargs["presence_penalty"]
        if "frequency_penalty" in kwargs:
            request["frequency_penalty"] = kwargs["frequency_penalty"]
            
        return request
    
    async def _make_request(self, request: Dict[str, Any]) -> httpx.Response:
        url = f"{self.config.base_url}/chat/completions"
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
            "text": data["choices"][0]["message"]["content"],
            "raw_response": data
        }
    
    async def _process_stream(self, response: httpx.Response) -> AsyncIterator[str]:
        buffer = ""
        async for line in response.aiter_lines():
            if not line.strip():
                continue
                
            if line.startswith("data: "):
                line = line.removeprefix("data: ").strip()
                if line == "[DONE]":
                    break
                    
                try:
                    chunk = json.loads(line)
                    if delta := chunk["choices"][0]["delta"].get("content", ""):
                        buffer += delta
                        if delta.endswith((" ", ".", ",", "!", "?", "\n")):
                            await asyncio.sleep(0.05)  # Small delay for readability
                            yield buffer
                            buffer = ""
                except json.JSONDecodeError:
                    if self.config.debug:
                        print(f"Failed to decode chunk: {line}")
                    continue
                    
        if buffer:  # Yield any remaining text
            yield buffer 