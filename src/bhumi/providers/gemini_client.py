from ..base_client import BaseLLMClient, LLMConfig
from typing import Dict, Any, AsyncIterator, List
import json
import asyncio

class GeminiLLM:
    """Gemini implementation using BaseLLMClient"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        if not config.base_url:
            config.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.client = BaseLLMClient(config)
        
    async def completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Any:
        # Extract actual model name if it contains provider prefix
        model = self.config.model.split('/')[-1] if '/' in self.config.model else self.config.model
        
        # Get the prompt from first message
        prompt = messages[0]["content"] if messages else ""
        
        request = {
            "_headers": {
                "Authorization": self.config.api_key  # Raw API key
            },
            "contents": [{
                "parts": [{
                    "text": prompt
                }],
                "role": "user"
            }],
            "stream": stream,
            **kwargs
        }
        
        if stream:
            return self._stream_completion(request)
        
        response = await self.client.completion(request)
        # Parse response in Python
        if isinstance(response, str):
            response = json.loads(response)
        return response
    
    async def _stream_completion(self, request: Dict[str, Any]) -> AsyncIterator[str]:
        """Handle streaming responses"""
        async for chunk in await self.client.completion(request, stream=True):
            yield chunk 