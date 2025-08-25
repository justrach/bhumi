from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any, Union
from dataclasses import dataclass
from .utils import async_retry
import os
import bhumi.bhumi as _rust

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    api_key: str
    model: str  # Format: "provider/model_name" e.g. "gemini/gemini-pro" or "openai/gpt-4"
    base_url: Optional[str] = None  # Now optional, will be set in __post_init__
    api_version: Optional[str] = None
    organization: Optional[str] = None
    max_retries: int = 3
    timeout: float = 30.0
    headers: Optional[Dict[str, str]] = None
    debug: bool = False
    max_tokens: Optional[int] = None
    extra_config: Dict[str, Any] = None
    buffer_size: int = 16384  # Added buffer size parameter with 16KB default

    def __post_init__(self):
        """Set up provider-specific configuration after initialization"""
        provider = self.provider
        
        # Set default base URLs based on provider
        if not self.base_url:
            if provider == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif provider == "anthropic":
                self.base_url = "https://api.anthropic.com/v1"
            elif provider == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        
        # Set provider-specific headers
        self.headers = self.headers or {}
        if provider == "openai":
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        elif provider == "anthropic":
            self.headers["x-api-key"] = self.api_key
            self.headers["anthropic-version"] = self.api_version or "2023-06-01"
        elif provider == "gemini":
            # Gemini with OpenAI-compatible endpoint uses Bearer token
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    @property
    def provider(self) -> str:
        """Extract provider from model string"""
        return self.model.split("/")[0]

    @property
    def model_name(self) -> str:
        """Extract model name from model string"""
        return self.model.split("/")[1]

def create_llm(config: LLMConfig) -> 'BaseLLM':
    """Factory function to create appropriate LLM client"""
    if config.provider == "gemini":
        from .providers.gemini_client import GeminiLLM
        return GeminiLLM(config)
    elif config.provider == "anthropic":
        from .providers.anthropic_client import AnthropicLLM
        return AnthropicLLM(config)
    else:
        from .providers.openai_client import OpenAILLM
        return OpenAILLM(config)

class BaseLLM(ABC):
    """Base class for LLM providers following OpenAI-like interface"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._setup_client()
    
    @abstractmethod
    def _setup_client(self) -> Any:
        """Setup the HTTP client with appropriate configuration"""
        pass
    
    @abstractmethod
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests"""
        base_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        if self.config.headers:
            base_headers.update(self.config.headers)
        return base_headers
    
    @abstractmethod
    def _prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Prepare the request body"""
        return {
            "model": self.config.model,
            "messages": messages,
            **kwargs
        }
    
    @abstractmethod
    async def _process_response(self, response: Any) -> Dict[str, Any]:
        """Process the API response"""
        pass
    
    @abstractmethod
    async def _process_stream(self, stream: Any) -> AsyncIterator[str]:
        """Process streaming response"""
        pass

    @async_retry(max_retries=3)
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
        request = self._prepare_request(messages, stream=stream, **kwargs)
        
        if stream:
            return self._stream_completion(request)
        return await self._regular_completion(request)
    
    async def _regular_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle non-streaming completion"""
        response = await self._make_request(request)
        return await self._process_response(response)
    
    async def _stream_completion(self, request: Dict[str, Any]) -> AsyncIterator[str]:
        """Handle streaming completion"""
        stream = await self._make_streaming_request(request)
        async for chunk in self._process_stream(stream):
            yield chunk
    
    @abstractmethod
    async def _make_request(self, request: Dict[str, Any]) -> Any:
        """Make a regular API request"""
        pass
    
    @abstractmethod
    async def _make_streaming_request(self, request: Dict[str, Any]) -> Any:
        """Make a streaming API request"""
        pass 

    def __init__(
        self,
        config: LLMConfig,
        max_concurrent: int = 10,
        debug: bool = False,
        debug_debug: bool = False,
    ):
        self.config = config
        # Resolve flags with env overrides
        debug = debug
        debug_debug = debug_debug or (os.environ.get("BHUMI_DEBUG_DEBUG", "0") == "1")
        self.core = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider=config.provider or "generic",
            model=config.model,
            debug=debug,
            debug_debug=debug_debug,
            base_url=config.base_url,
            buffer_size=config.buffer_size,  # Pass buffer_size to Rust
        )
        self.debug = debug 