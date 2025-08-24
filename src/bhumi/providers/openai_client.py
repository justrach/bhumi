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
        
    async def completion(self, messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Any:
        response = await self.client.completion(messages, stream=stream, **kwargs)
        if stream:
            return self._handle_stream(response)
        return response
    
    async def _handle_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for chunk in stream:
            yield chunk 

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str = "1024x1024",
        n: int = 1,
        response_format: str = "b64_json",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Forward image generation to BaseLLMClient."""
        return await self.client.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            n=n,
            response_format=response_format,
            **kwargs,
        )

    def register_image_tool(self) -> None:
        """Expose the image generation tool to the model."""
        return self.client.register_image_tool()