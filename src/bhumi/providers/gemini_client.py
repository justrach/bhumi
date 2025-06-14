from typing import Dict, List, Optional, AsyncGenerator, Union
from ..base_client import BaseLLMClient, LLMConfig

class GeminiClient:
    """Simple client for Gemini API that uses BaseLLMClient for HTTP requests"""
    
    def __init__(self, config: LLMConfig, client: BaseLLMClient):
        # BaseLLMClient already handles everything through Rust core
        self.client = client
        
    async def completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs):
        """Forward completion request to BaseLLMClient"""
        return await self.client.completion(messages, stream=stream, **kwargs)

# Legacy compatibility alias - just return BaseLLMClient directly
class GeminiLLM(BaseLLMClient):
    """Legacy alias that returns BaseLLMClient directly for backward compatibility"""
    
    def __init__(self, config: LLMConfig):
        # Just create BaseLLMClient directly - it handles everything through Rust
        super().__init__(config)