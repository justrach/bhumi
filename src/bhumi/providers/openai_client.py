import asyncio
from ..base_client import BaseLLMClient, LLMConfig
from typing import Dict, Any, AsyncIterator, List

class OpenAILLM:
    """OpenAI implementation using BaseLLMClient directly"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        if not config.base_url:
            config.base_url = "https://api.openai.com/v1"
        self.client = BaseLLMClient(config)
        
    async def completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Any:
        response = await self.client.completion(messages, stream=stream, **kwargs)
        if stream:
            return self._handle_stream(response)
        return response
    
    async def _handle_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for chunk in stream:
            yield chunk 