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
    model: str  # Format: "provider/model_name" e.g. "openai/gpt-4"
    base_url: Optional[str] = None  # Now optional
    provider: Optional[str] = None  # Optional, extracted from model if not provided
    api_version: Optional[str] = None
    organization: Optional[str] = None
    max_retries: int = 3
    timeout: float = 30.0
    headers: Optional[Dict[str, str]] = None
    debug: bool = False
    max_tokens: Optional[int] = None  # Add max_tokens parameter
    extra_config: Dict[str, Any] = None
    buffer_size: int = 131072  # Back to 128KB for optimal performance

    def __post_init__(self):
        # Extract provider from model if not provided
        if not self.provider and "/" in self.model:
            self.provider = self.model.split("/")[0]
        
        # Set default base URL if not provided
        if not self.base_url:
            if self.provider == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == "anthropic":
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1/models"
            elif self.provider == "sambanova":
                self.base_url = "https://api.sambanova.ai/v1"
            elif self.provider == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            else:
                self.base_url = "https://api.openai.com/v1"  # Default to OpenAI

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
            provider=config.provider or "generic",
            model=config.model,
            debug=debug,
            base_url=config.base_url,
            buffer_size=config.buffer_size,  # Pass buffer_size to Rust
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
        
        # Extract actual model name if it contains provider prefix
        model = self.config.model.split('/')[-1] if '/' in self.config.model else self.config.model
        
        # Prepare headers based on provider
        if self.config.provider == "anthropic":
            headers = {
                "x-api-key": self.config.api_key
            }
        else:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"  # For OpenAI, Gemini etc
            }
        
        # Prepare request with required fields
        request = {
            "_headers": headers,
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": kwargs.pop("max_tokens", 1024) if self.config.provider == "anthropic" else None,
            **kwargs
        }
        
        if self.debug:
            print(f"Sending request with model: {model}")
            print(f"Headers: {request['_headers']}")
        
        # Submit request
        self.core._submit(json.dumps(request))
        
        # Wait for response
        while True:
            if response := self.core._get_response():
                try:
                    response_data = json.loads(response)
                    # Handle Gemini's response format
                    if "candidates" in response_data:
                        return {
                            "text": response_data["candidates"][0]["content"]["parts"][0]["text"],
                            "raw_response": response_data
                        }
                    # Handle OpenAI/other formats
                    elif "choices" in response_data:
                        return {
                            "text": response_data["choices"][0]["message"]["content"],
                            "raw_response": response_data
                        }
                    # Fallback for other response formats
                    else:
                        return {
                            "text": response,
                            "raw_response": {"text": response}
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
        model = self.config.model.split('/')[-1] if '/' in self.config.model else self.config.model
        
        headers = {
            "x-api-key": self.config.api_key if self.config.provider == "anthropic" else f"Bearer {self.config.api_key}"
        }
        
        request = {
            "model": model,
            "messages": messages,
            "stream": True,
            "_headers": headers,
            "max_tokens": kwargs.pop("max_tokens", 1024),
            **kwargs
        }
        
        self.core._submit(json.dumps(request))
        
        while True:
            chunk = self.core._get_stream_chunk()
            if chunk == "[DONE]":
                break
            if chunk:
                try:
                    data = json.loads(chunk)
                    if self.config.provider == "anthropic":
                        # Handle Anthropic's SSE format
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                        elif data.get("type") == "message_stop":
                            break
                    else:
                        # Handle other providers
                        yield chunk
                except json.JSONDecodeError:
                    # If not JSON, yield raw chunk
                    yield chunk
            await asyncio.sleep(0.01) 