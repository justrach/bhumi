import json
import sys
from typing import List, Dict, Optional, Union, AsyncIterator, Any
from dataclasses import dataclass
import asyncio
import time

# Get the root module (the Rust implementation)
import bhumi.bhumi as _rust
from .models.openai import OpenAIResponse, Message, Choice, Usage, TokenDetails, CompletionTokenDetails, OpenAIStreamChunk

# Export BhumiCore directly from _rust
BhumiCore = _rust.BhumiCore

# Export in __all__
__all__ = ['OpenAIClient', 'BhumiCore']

@dataclass
class CompletionResponse:
    text: str
    raw_response: dict
    
    @classmethod
    def from_raw_response(cls, response: str, provider: str = "gemini") -> 'CompletionResponse':
        try:
            response_json = json.loads(response)
            
            # Fast path: if text is directly available, use it
            if isinstance(response_json, str):
                return cls(text=response_json, raw_response={"text": response_json})
                
            # Provider-specific parsing
            text = None
            if provider == "gemini":
                if "candidates" in response_json:
                    text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            elif provider == "openai":
                if "choices" in response_json:
                    text = response_json["choices"][0]["message"]["content"]
            elif provider == "anthropic":
                if "content" in response_json:
                    text = response_json["content"][0]["text"]
            
            # Fallback: use the entire response as text if we couldn't parse it
            if text is None:
                text = response
                
            return cls(text=text, raw_response=response_json)
        except json.JSONDecodeError:
            # If we can't parse as JSON, use raw text
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

    async def astream_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming completion call"""
        request = {
            "_headers": {
                "Authorization": api_key
            },
            "model": model.split('/', 1)[1] if '/' in model else model,
            "messages": messages,
            "stream": True
        }
        
        self._client._submit(json.dumps(request))
        
        # Wait for streaming responses
        start_time = time.time()
        
        while True:
            chunk = self._client._get_stream_chunk()
            if chunk == "[DONE]":
                break
            
            if chunk:
                yield chunk
            
            if time.time() - start_time > 30:
                raise TimeoutError("Stream timeout")
            
            await asyncio.sleep(0.01)  # Reduced sleep time

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
    ) -> CompletionResponse:
        """Async OpenAI completion call"""
        request = {
            "_headers": {
                "Authorization": api_key
            },
            "model": model.split('/', 1)[1] if '/' in model else model,
            "messages": messages,
            "stream": False
        }
        
        self._client._submit(json.dumps(request))
        
        # Wait for response with timeout
        start_time = time.time()
        while True:
            response = self._client._get_response()
            if response:
                try:
                    response_data = json.loads(response)
                    # Skip validation for now and directly create object
                    response_obj = OpenAIResponse(
                        id=response_data["id"],
                        object=response_data["object"],
                        created=response_data["created"],
                        model=response_data["model"],
                        choices=[
                            Choice(
                                index=c["index"],
                                message=Message(
                                    role=c["message"]["role"],
                                    content=c["message"]["content"],
                                    refusal=c["message"].get("refusal")
                                ),
                                logprobs=c.get("logprobs"),
                                finish_reason=c["finish_reason"]
                            ) for c in response_data["choices"]
                        ],
                        usage=Usage(
                            prompt_tokens=response_data["usage"]["prompt_tokens"],
                            completion_tokens=response_data["usage"]["completion_tokens"],
                            total_tokens=response_data["usage"]["total_tokens"],
                            prompt_tokens_details=TokenDetails(
                                cached_tokens=response_data["usage"]["prompt_tokens_details"]["cached_tokens"],
                                audio_tokens=response_data["usage"]["prompt_tokens_details"]["audio_tokens"]
                            ),
                            completion_tokens_details=CompletionTokenDetails(
                                reasoning_tokens=response_data["usage"]["completion_tokens_details"]["reasoning_tokens"],
                                audio_tokens=response_data["usage"]["completion_tokens_details"]["audio_tokens"],
                                accepted_prediction_tokens=response_data["usage"]["completion_tokens_details"]["accepted_prediction_tokens"],
                                rejected_prediction_tokens=response_data["usage"]["completion_tokens_details"]["rejected_prediction_tokens"]
                            )
                        ),
                        service_tier=response_data["service_tier"],
                        system_fingerprint=response_data.get("system_fingerprint")
                    )
                    return CompletionResponse(
                        text=response_obj.choices[0].message.content,
                        raw_response=response_data
                    )
                except Exception as e:
                    if self.debug:
                        print(f"Error parsing response: {e}")
                    return CompletionResponse(
                        text=response,
                        raw_response={"text": response}
                    )
            
            if time.time() - start_time > 30:
                raise TimeoutError("Request timed out")
            
            await asyncio.sleep(0.1)