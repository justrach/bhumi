import json
import sys
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import asyncio
import time

# Get the root module (the Rust implementation)
import bhumi.bhumi as _rust

@dataclass
class CompletionResponse:
    text: str
    raw_response: dict
    
    @classmethod
    def from_raw_response(cls, response: str, provider: str = "gemini") -> 'CompletionResponse':
        try:
            response_json = json.loads(response)
            
            if provider == "gemini":
                text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            elif provider == "openai":
                # Try to parse as OpenAI response first
                if "choices" in response_json:
                    text = response_json["choices"][0]["message"]["content"]
                else:
                    # If not a proper OpenAI response, use the raw text
                    text = response
            elif provider == "anthropic":
                text = response_json["content"][0]["text"]
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
            return cls(text=text, raw_response=response_json)
        except json.JSONDecodeError:
            # If we can't parse as JSON, assume it's raw text
            return cls(text=response, raw_response={"text": response})

class AsyncLLMClient:
    def __init__(
        self,
        max_concurrent: int = 30,
        provider: str = "gemini",
        model: str = "gemini-1.5-flash-8b",
        debug: bool = False
    ):
        self._client = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider=provider,
            model=model,
            debug=debug
        )
        self.provider = provider
        self.model = model
        self._response_queue = asyncio.Queue()
        self._response_task = None
        self.debug = debug  # Add debug flag

    async def _get_responses(self):
        """Background task to get responses from Rust"""
        while True:
            if response := self._client._get_response():
                await self._response_queue.put(response)
            await asyncio.sleep(0.001)  # Small delay to prevent busy waiting

    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        **kwargs
    ) -> CompletionResponse:
        """
        Async completion call
        """
        if self._response_task is None:
            self._response_task = asyncio.create_task(self._get_responses())

        provider, model_name = model.split('/', 1) if '/' in model else (self.provider, model)
        
        request = {
            "_headers": {
                "Authorization": api_key  # No Bearer prefix - Rust code adds it
            },
            "model": model_name,
            "messages": messages,
            "stream": False
        }
        
        if self.debug:
            print("DEBUG: Sending request:", json.dumps(request, indent=2))
            
        self._client._submit(json.dumps(request))
        
        # Wait for response
        response = await self._response_queue.get()
        
        if self.debug:
            print("DEBUG: Got response:", response)
            
        return CompletionResponse.from_raw_response(response, provider=provider)

# Provider-specific clients
class GeminiClient(AsyncLLMClient):
    def __init__(
        self,
        max_concurrent: int = 30,
        model: str = "gemini-1.5-flash-8b",
        debug: bool = False
    ):
        super().__init__(
            max_concurrent=max_concurrent,
            provider="gemini",
            model=model,
            debug=debug
        )

class AnthropicClient(AsyncLLMClient):
    def __init__(
        self,
        max_concurrent: int = 30,
        model: str = "claude-3-haiku",
        debug: bool = False
    ):
        super().__init__(
            max_concurrent=max_concurrent,
            provider="anthropic",
            model=model,
            debug=debug
        )

class OpenAIClient(AsyncLLMClient):
    def __init__(
        self,
        max_concurrent: int = 30,
        model: str = "gpt-4o",
        debug: bool = False
    ):
        self._client = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider="openai",
            model=model,
            debug=debug
        )
        self.debug = debug

    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        **kwargs
    ) -> CompletionResponse:
        """Async OpenAI completion call"""
        # Prepare request
        request = {
            "_headers": {
                "Authorization": api_key
            },
            "model": model.split('/', 1)[1] if '/' in model else model,
            "messages": messages,
            "stream": False
        }
        
        if self.debug:
            print(f"Request payload: {json.dumps(request, indent=2)}")
        
        # Submit request
        self._client._submit(json.dumps(request))
        
        # Wait for response with timeout
        start_time = time.time()
        while True:
            if response := self._client._get_response():
                if self.debug:
                    print("\nReceived response:")
                    print("=" * 40)
                    print(response)
                    print("=" * 40)
                return CompletionResponse(
                    text=response,
                    raw_response={"text": response}
                )
            elif time.time() - start_time > 30:  # 30 second timeout
                raise TimeoutError("Request timed out")
            await asyncio.sleep(0.1)  # Use asyncio.sleep for async waiting