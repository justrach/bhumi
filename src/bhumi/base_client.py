from dataclasses import dataclass
from typing import Optional, Dict, List, Union, AsyncIterator, Any
from .utils import async_retry
import bhumi.bhumi as _rust
import json
import asyncio

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    api_key: str
    base_url: str
    model: str
    provider: Optional[str] = None  # Optional now, defaults to OpenAI-compatible
    api_version: Optional[str] = None
    organization: Optional[str] = None
    max_retries: int = 3
    timeout: float = 30.0
    headers: Optional[Dict[str, str]] = None
    debug: bool = False

class BaseLLMClient:
    """Generic client for OpenAI-compatible APIs"""
    
    def __init__(
        self,
        config: LLMConfig,
        max_concurrent: int = 10,
        debug: bool = False
    ):
        self.config = config
        self.core = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider=config.provider or "generic",  # Use generic if no provider specified
            model=config.model,
            debug=debug,
            base_url=config.base_url
        )
        self.debug = debug
    
    async def completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """
        Send a completion request to the LLM provider
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Either a complete response or an async iterator for streaming
        """
        if stream:
            return self.astream_completion(messages, **kwargs)
        
        # Prepare the request
        request = {
            "_headers": {
                "Authorization": self.config.api_key
            },
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        # Submit request
        self.core._submit(json.dumps(request))
        
        # Wait for response
        while True:
            if response := self.core._get_response():
                try:
                    response_data = json.loads(response)
                    return {
                        "text": response_data["choices"][0]["message"]["content"],
                        "raw_response": response_data
                    }
                except Exception as e:
                    if self.debug:
                        print(f"Error parsing response: {e}")
                    return {
                        "text": response,
                        "raw_response": {"text": response}
                    }
            await asyncio.sleep(0.1)
    
    async def astream_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion responses"""
        request = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "_headers": {
                "Authorization": self.config.api_key
            },
            **kwargs
        }
        
        self.core._submit(json.dumps(request))
        
        while True:
            chunk = self.core._get_stream_chunk()
            if chunk == "[DONE]":
                break
            if chunk:
                yield chunk
            await asyncio.sleep(0.01) 