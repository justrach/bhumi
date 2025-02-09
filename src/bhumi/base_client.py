from dataclasses import dataclass
from typing import Optional, Dict, List, Union, AsyncIterator, Any
from .utils import async_retry
import bhumi.bhumi as _rust
import json
import asyncio
import os
from .map_elites_buffer import MapElitesBuffer
import statistics

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

class DynamicBuffer:
    """Original dynamic buffer implementation"""
    def __init__(self, initial_size=8192, min_size=1024, max_size=131072):
        self.current_size = initial_size
        self.min_size = min_size
        self.max_size = max_size
        self.chunk_history = []
        self.adjustment_factor = 1.5
        
    def get_size(self) -> int:
        return self.current_size
        
    def adjust(self, chunk_size):
        self.chunk_history.append(chunk_size)
        recent_chunks = self.chunk_history[-5:]
        avg_chunk = statistics.mean(recent_chunks) if recent_chunks else chunk_size
        
        if avg_chunk > self.current_size * 0.8:
            self.current_size = min(
                self.max_size,
                int(self.current_size * self.adjustment_factor)
            )
        elif avg_chunk < self.current_size * 0.3:
            self.current_size = max(
                self.min_size,
                int(self.current_size / self.adjustment_factor)
            )
        return self.current_size

class BaseLLMClient:
    """Generic client for OpenAI-compatible APIs"""
    
    def __init__(
        self,
        config: LLMConfig,
        max_concurrent: int = 10,
        debug: bool = False
    ):
        self.config = config
        self.max_concurrent = max_concurrent
        self.debug = debug
        
        # Create initial core
        self.core = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider=config.provider or "generic",
            model=config.model,
            debug=debug,
            base_url=config.base_url
        )
        
        # Only initialize buffer strategy for non-streaming requests
        archive_paths = [
            "src/archive_latest.json",
            "benchmarks/map_elites/archive_latest.json",
            os.path.join(os.path.dirname(__file__), "../archive_latest.json"),
            os.path.join(os.path.dirname(__file__), "../../benchmarks/map_elites/archive_latest.json")
        ]
        
        for path in archive_paths:
            if os.path.exists(path):
                if debug:
                    print(f"Loading MAP-Elites archive from: {path}")
                self.buffer_strategy = MapElitesBuffer(archive_path=path)
                break
        else:
            if debug:
                print("No MAP-Elites archive found, using dynamic buffer")
            self.buffer_strategy = DynamicBuffer()

    async def completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Send a completion request to the LLM provider"""
        if stream:
            return self.astream_completion(messages, **kwargs)
        
        # For non-streaming, use adaptive buffer strategy
        buffer_size = self.buffer_strategy.get_size()
        if self.debug:
            print(f"Using buffer size: {buffer_size}")
            
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
        
        if self.debug:
            print(f"Sending streaming request for {self.config.provider}")
        
        self.core._submit(json.dumps(request))
        
        while True:
            chunk = self.core._get_stream_chunk()
            if chunk == "[DONE]":
                break
            if chunk:
                try:
                    if self.debug:
                        print(f"Received chunk: {chunk}")
                        
                    # First try parsing the chunk as JSON
                    data = json.loads(chunk)
                    
                    # Skip if data is not a dictionary
                    if not isinstance(data, dict):
                        continue
                        
                    if self.config.provider == "anthropic":
                        # Handle Anthropic's SSE format
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                        elif data.get("type") == "message_stop":
                            break
                    elif self.config.provider == "gemini":
                        # Handle Gemini's format
                        if "candidates" in data:
                            text = (data.get("candidates", [{}])[0]
                                   .get("content", {})
                                   .get("parts", [{}])[0]
                                   .get("text", ""))
                            if text:
                                yield text
                    else:
                        # Handle OpenAI and other providers
                        if "choices" in data:
                            choice = data["choices"][0]
                            if "delta" in choice:
                                delta = choice["delta"]
                                if "content" in delta:
                                    if self.debug:
                                        print(f"Yielding content: {delta['content']}")
                                    yield delta["content"]
                            
                            # Check for finish reason
                            if choice.get("finish_reason"):
                                break
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract content from raw SSE data
                    if chunk.startswith("data: "):
                        data = chunk.removeprefix("data: ")
                        if data != "[DONE]":
                            try:
                                parsed = json.loads(data)
                                if isinstance(parsed, dict) and "choices" in parsed:
                                    content = (parsed.get("choices", [{}])[0]
                                             .get("delta", {})
                                             .get("content"))
                                    if content:
                                        if self.debug:
                                            print(f"Yielding from SSE: {content}")
                                        yield content
                            except json.JSONDecodeError:
                                if self.debug:
                                    print(f"Failed to parse SSE data: {data}")
                                yield data
            await asyncio.sleep(0.01) 