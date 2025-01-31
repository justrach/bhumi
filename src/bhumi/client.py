import json
import sys
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import asyncio
import time
from pydantic import BaseModel

from .models.openai import OpenAIResponse, OpenAIRequest, Message

# Get the root module (the Rust implementation)
import bhumi.bhumi as _rust

class CompletionResponse(BaseModel):
    text: str
    raw_response: Dict
    
    @classmethod
    def from_raw_response(cls, response: str, provider: str = "gemini") -> 'CompletionResponse':
        try:
            response_json = json.loads(response)
            
            if isinstance(response_json, str):
                return cls(text=response_json, raw_response={"text": response_json})
            
            # Provider-specific parsing with Pydantic
            text = None
            if provider == "openai":
                parsed_response = OpenAIResponse.model_validate(response_json)
                text = parsed_response.text
            elif provider == "gemini":
                if "candidates" in response_json:
                    text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            elif provider == "anthropic":
                if "content" in response_json:
                    text = response_json["content"][0]["text"]
            
            if text is None:
                text = response
                
            return cls(text=text, raw_response=response_json)
        except json.JSONDecodeError:
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
        model: str = "gpt-4",
        debug: bool = False
    ):
        super().__init__(
            max_concurrent=max_concurrent,
            provider="openai",
            model=model,
            debug=debug
        )

    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        **kwargs
    ) -> OpenAIResponse:
        """Async OpenAI completion call with Pydantic models"""
        # Convert messages to Pydantic models
        pydantic_messages = [Message(**msg) for msg in messages]
        
        # Create request using Pydantic model
        request = OpenAIRequest(
            model=model.split('/', 1)[1] if '/' in model else model,
            messages=pydantic_messages,
            stream=False,
            **kwargs
        )
        
        # Convert to dict for JSON serialization
        request_dict = request.model_dump(exclude_none=True)
        request_dict["_headers"] = {"Authorization": api_key}
        
        if self.debug:
            print(f"Request payload: {json.dumps(request_dict, indent=2)}")
        
        self._client._submit(json.dumps(request_dict))
        
        start_time = time.time()
        while True:
            if response := self._client._get_response():
                if self.debug:
                    print(f"\nReceived response:\n{'=' * 40}\n{response}\n{'=' * 40}")
                
                # Parse response using Pydantic model
                response_data = json.loads(response)
                return OpenAIResponse.model_validate(response_data)
                
            elif time.time() - start_time > 30:
                raise TimeoutError("Request timed out")
            await asyncio.sleep(0.1)