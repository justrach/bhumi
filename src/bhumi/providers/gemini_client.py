from typing import Dict, List, Optional, AsyncGenerator, Union
from openai import AsyncOpenAI
from ..base_client import BaseLLMClient, LLMConfig

class GeminiClient:
    """Client for Gemini's API using OpenAI-compatible endpoints"""
    
    def __init__(self, config: LLMConfig, client: BaseLLMClient):
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model = config.model.replace("gemini/", "")  # Remove gemini/ prefix if present
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    async def completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, str], AsyncGenerator[str, None]]:
        """Send a completion request to Gemini"""
        
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        
        if stream:
            return self._stream_response(response)
        else:
            return {
                "text": response.choices[0].message.content,
                "raw": response.model_dump()
            }
    
    async def _stream_response(self, response) -> AsyncGenerator[str, None]:
        """Handle streaming response"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# Legacy compatibility alias
class GeminiLLM(GeminiClient):
    """Legacy alias for GeminiClient for backward compatibility"""
    
    def __init__(self, config: LLMConfig):
        # Initialize with a dummy BaseLLMClient for compatibility
        super().__init__(config, None)