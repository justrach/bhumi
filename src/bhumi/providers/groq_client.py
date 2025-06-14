from typing import Dict, List, Optional, AsyncGenerator, Union
from ..base_client import BaseLLMClient, LLMConfig

class GroqClient:
    """Simple client for Groq API that uses BaseLLMClient for HTTP requests"""
    
    def __init__(self, config: LLMConfig, client: BaseLLMClient):
        # BaseLLMClient already handles everything through Rust core
        self.client = client
        
    async def completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs):
        """Forward completion request to BaseLLMClient"""
        return await self.client.completion(messages, stream=stream, **kwargs)