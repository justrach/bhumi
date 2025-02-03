from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any, Union
from dataclasses import dataclass
from .utils import async_retry

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    api_key: str
    base_url: str
    model: str
    api_version: Optional[str] = None
    organization: Optional[str] = None
    max_retries: int = 3
    timeout: float = 30.0
    headers: Optional[Dict[str, str]] = None
    debug: bool = False

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