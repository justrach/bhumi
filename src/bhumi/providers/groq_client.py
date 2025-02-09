from typing import Dict, List, Optional, AsyncGenerator, Union
from openai import AsyncOpenAI
from ..base_client import BaseLLMClient, LLMConfig, LLMResponse

class GroqClient:
    """Client for Groq's API using OpenAI-compatible endpoints"""
    
    def __init__(self, config: LLMConfig, client: BaseLLMClient):
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.groq.com/openai/v1"
        self.model = config.model.replace("groq/", "")  # Remove groq/ prefix if present
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    async def completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Send a completion request to Groq"""
        
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        
        if stream:
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            return {
                "text": response.choices[0].message.content,
                "raw": response.model_dump()
            } 