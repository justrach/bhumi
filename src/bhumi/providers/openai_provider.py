from ..base import BaseLLM, LLMConfig
import httpx
from typing import Dict, Any, AsyncIterator
import json

class OpenAILLM(BaseLLM):
    """OpenAI implementation of BaseLLM"""
    
    def _setup_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._prepare_headers()
        )
    
    def _prepare_headers(self) -> Dict[str, str]:
        headers = super()._prepare_headers()
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        return headers
    
    def _prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        request = super()._prepare_request(messages, **kwargs)
        # Add OpenAI-specific parameters
        request.update({
            "temperature": kwargs.get("temperature", 1.0),
            "max_tokens": kwargs.get("max_tokens", None),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        })
        return request
    
    async def _make_request(self, request: Dict[str, Any]) -> httpx.Response:
        response = await self.client.post(
            f"{self.config.base_url}/chat/completions",
            json=request
        )
        response.raise_for_status()
        return response
    
    async def _make_streaming_request(self, request: Dict[str, Any]) -> httpx.Response:
        request["stream"] = True
        return await self._make_request(request)
    
    async def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        data = response.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "raw_response": data
        }
    
    async def _process_stream(self, response: httpx.Response) -> AsyncIterator[str]:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                if line.strip() == "data: [DONE]":
                    break
                chunk = json.loads(line.removeprefix("data: "))
                if content := chunk["choices"][0]["delta"].get("content"):
                    yield content 