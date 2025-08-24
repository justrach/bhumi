from dataclasses import dataclass
from typing import Optional, Dict, List, Union, AsyncIterator, Any, Callable, Type, get_type_hints
from .utils import async_retry, extract_json_from_text, parse_json_loosely
import bhumi.bhumi as _rust
import json
import asyncio
import os
import base64
from .map_elites_buffer import MapElitesBuffer
import statistics
from .tools import ToolRegistry, Tool, ToolCall
import uuid
import re
from pydantic import BaseModel, create_model
import inspect

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
        
        # Normalize provider alias ending with '!'
        if self.provider and self.provider.endswith("!"):
            self.provider = self.provider[:-1]
        
        # Set default base URL if not provided
        if not self.base_url:
            if self.provider == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == "anthropic":
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            elif self.provider == "sambanova":
                self.base_url = "https://api.sambanova.ai/v1"
            elif self.provider == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            elif self.provider == "cerebras":
                self.base_url = "https://api.cerebras.ai/v1"
            elif self.provider == "openrouter":
                self.base_url = "https://openrouter.ai/api/v1"
            else:
                self.base_url = "https://api.openai.com/v1"  # Default to OpenAI

def parse_streaming_chunk(chunk: str, provider: str) -> str:
    """Parse streaming response chunk based on provider format"""
    try:
        # Handle Server-Sent Events format
        lines = chunk.strip().split('\n')
        content_parts = []
        
        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                if data_str.strip() == '[DONE]':
                    continue
                    
                try:
                    data = json.loads(data_str)
                    
                    # Extract content based on provider format
                    if provider in ['openai', 'groq', 'openrouter', 'sambanova', 'gemini', 'cerebras']:
                        # OpenAI-compatible format
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                content_parts.append(delta['content'])
                    elif provider == 'anthropic':
                        # Anthropic format (different streaming format)
                        if 'delta' in data and 'text' in data['delta']:
                            content_parts.append(data['delta']['text'])
                except json.JSONDecodeError:
                    # If not JSON, might be plain text chunk
                    if data_str.strip():
                        content_parts.append(data_str)
            elif line.strip() and not line.startswith(':'):
                # Plain text line (fallback)
                content_parts.append(line)
        
        return ''.join(content_parts)
    except Exception:
        # Fallback: return original chunk
        return chunk

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

@dataclass
class ReasoningResponse:
    """Special response class for reasoning models"""
    _reasoning: str
    _output: str
    _raw: dict
    
    @property
    def think(self) -> str:
        """Get the model's reasoning process"""
        return self._reasoning
    
    def __str__(self) -> str:
        """Default to showing just the output"""
        return self._output

class StructuredOutput:
    """Handler for structured output from LLM responses"""
    
    def __init__(self, output_type: Type[BaseModel]):
        self.output_type = output_type
        self._schema = output_type.model_json_schema()
    
    def to_tool_schema(self) -> dict:
        """Convert Pydantic model to function parameters schema"""
        return {
            "type": "object",
            "properties": self._schema.get("properties", {}),
            "required": self._schema.get("required", []),
            "additionalProperties": False
        }
    
    def parse_response(self, response: str) -> BaseModel:
        """Parse LLM response into structured output"""
        # Strict JSON first
        try:
            data = json.loads(response)
            return self.output_type.model_validate(data)
        except json.JSONDecodeError:
            pass

        # Loose extraction from text
        data = parse_json_loosely(response)
        if data is not None:
            return self.output_type.model_validate(data)

        raise ValueError("Response is not in structured format")
    
    def _extract_structured_data(self, text: str) -> BaseModel:
        """Extract structured data from text response"""
        # Add extraction logic here
        # For now, just raise an error
        raise ValueError("Response is not in structured format")

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
        # Look for MAP-Elites archive in multiple locations
        archive_paths = [
            # First, look in the installed package data directory
            os.path.join(os.path.dirname(__file__), "data", "archive_latest.json"),
            # Then look in development locations
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
        
        # Add tool registry
        self.tool_registry = ToolRegistry()
        self.structured_output = None

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Register a new tool that can be called by the model"""
        self.tool_registry.register(name, func, description, parameters)

    def set_structured_output(self, model: Type[BaseModel]) -> None:
        """Set up structured output handling with a Pydantic model"""
        self.structured_output = StructuredOutput(model)
        
        # Register a tool for structured output
        self.register_tool(
            name="generate_structured_output",
            func=self._structured_output_handler,
            description=f"Generate structured output according to the schema: {model.__doc__}",
            parameters=self.structured_output.to_tool_schema()
        )
    
    async def _structured_output_handler(self, **kwargs) -> dict:
        """Handle structured output generation"""
        try:
            return self.structured_output.output_type(**kwargs).model_dump()
        except Exception as e:
            raise ValueError(f"Failed to create structured output: {e}")

    async def _handle_tool_calls(
        self,
        messages: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        debug: bool = False
    ) -> List[Dict[str, Any]]:
        """Handle tool calls and append results to messages"""
        if debug:
            print("\nHandling tool calls...")
        
        # First add the assistant's message with tool calls
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        })
        
        # Then handle each tool call
        for tool_call in tool_calls:
            if debug:
                print(f"\nProcessing tool call: {json.dumps(tool_call, indent=2)}")
            
            # Create ToolCall object
            call = ToolCall(
                id=tool_call.get("id", str(uuid.uuid4())),
                type=tool_call["type"],
                function=tool_call["function"]
            )
            
            try:
                # Execute the tool
                if debug:
                    print(f"\nExecuting tool: {call.function['name']}")
                    print(f"Arguments: {call.function['arguments']}")
                
                result = await self.tool_registry.execute_tool(call)
                
                if debug:
                    print(f"Tool execution result: {result}")
                
                # Add tool result to messages
                tool_message = {
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": call.id
                }
                
                messages.append(tool_message)
                
                if debug:
                    print(f"Added tool message: {json.dumps(tool_message, indent=2)}")
                    
            except Exception as e:
                if debug:
                    print(f"Error executing tool {call.function['name']}: {e}")
                messages.append({
                    "role": "tool",
                    "content": f"Error: {str(e)}",
                    "tool_call_id": call.id
                })
        
        return messages

    async def completion(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        debug: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Modified completion method to handle tool calls"""
        # Set debug mode for this request
        debug = debug or self.debug
        
        if stream:
            return self.astream_completion(messages, **kwargs)
            
        # Add tools to request if any are registered
        if self.tool_registry.get_public_definitions():
            if self.config.provider == "anthropic":
                tools = self.tool_registry.get_anthropic_definitions()
            else:
                tools = self.tool_registry.get_public_definitions()
            kwargs["tools"] = tools
            if debug:
                print(f"\nRegistered tools ({self.config.provider}): {json.dumps(tools, indent=2)}")
            
        # Extract model name after provider
        # Foundation model providers (openai, anthropic, gemini) use simple provider/model format
        # Gateway providers (groq, openrouter, sambanova) may use provider/company/model format
        if '/' in self.config.model:
            parts = self.config.model.split('/')
            if self.config.provider in ['groq', 'openrouter', 'sambanova', 'cerebras']:
                # Gateway providers: keep everything after provider (handles company/model)
                model = "/".join(parts[1:])
                pass  # Gateway provider parsing
            else:
                # Foundation providers: just take model name after provider
                model = parts[1]
        else:
            model = self.config.model
        
        # Prepare headers based on provider
        if self.config.provider == "anthropic":
            headers = {
                "x-api-key": self.config.api_key
            }
        else:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
        
        # Remove debug from kwargs if present
        kwargs.pop('debug', None)
        
        # Prepare request
        # Only include max_tokens if provided (avoid null/None in provider payloads)
        req_max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)
        # Anthropic requires max_tokens; default if missing
        if self.config.provider == "anthropic" and req_max_tokens is None:
            req_max_tokens = 1024
        request = {
            "_headers": headers,
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        if req_max_tokens is not None:
            request["max_tokens"] = req_max_tokens
        
        # Gemini now uses OpenAI-compatible chat/completions path; no special formatting.
        
        # Provider-specific payload normalization
        if self.config.provider == "anthropic":
            # Transform messages to Anthropic block schema if needed
            norm_msgs = []
            for m in request.get("messages", []):
                content = m.get("content", "")
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                norm_msgs.append({"role": m.get("role", "user"), "content": content})
            request["messages"] = norm_msgs

        if debug:
            print(f"\nSending request: {json.dumps(request, indent=2)}")
        
        # Submit request
        self.core._submit(json.dumps(request))
        
        while True:
            if response := self.core._get_response():
                try:
                    if debug:
                        print(f"\nRaw response: {response}")
                    
                    response_data = json.loads(response)
                    
                    # Check for tool calls in response
                    if "tool_calls" in response_data.get("choices", [{}])[0].get("message", {}):
                        if debug:
                            print("\nFound tool calls in response")
                        
                        tool_calls = response_data["choices"][0]["message"]["tool_calls"]
                        
                        # Handle tool calls and update messages
                        messages = await self._handle_tool_calls(messages, tool_calls, debug)
                        
                        # Continue conversation with tool results
                        if debug:
                            print(f"\nContinuing conversation with updated messages: {json.dumps(messages, indent=2)}")
                        
                        # Make a new request with the updated messages
                        request["messages"] = messages
                        self.core._submit(json.dumps(request))
                        continue
                    
                    # For Gemini responses
                    if self.config.provider == "gemini":
                        if "candidates" in response_data:
                            candidate = response_data["candidates"][0]
                            
                            # Check for function calls
                            if "functionCall" in candidate:
                                if debug:
                                    print("\nFound function call in Gemini response")
                                
                                function_call = candidate["functionCall"]
                                tool_calls = [{
                                    "id": str(uuid.uuid4()),
                                    "type": "function",
                                    "function": {
                                        "name": function_call["name"],
                                        "arguments": function_call["args"]
                                    }
                                }]
                                
                                # Handle tool calls and update messages
                                messages = await self._handle_tool_calls(messages, tool_calls, debug)
                                
                                # Continue conversation with tool results
                                if debug:
                                    print(f"\nContinuing conversation with updated messages: {json.dumps(messages, indent=2)}")
                                
                                # Make a new request with the updated messages (OpenAI-compatible continuation)
                                request["messages"] = messages
                                self.core._submit(json.dumps(request))
                                continue
                            
                            # Handle regular response
                            text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                            return {
                                "text": text or str(response_data),
                                "raw_response": response_data
                            }
                    
                    # Handle responses in completion method
                    if "choices" in response_data:
                        message = response_data["choices"][0]["message"]
                        content = message.get("content", "")
                        
                        # First check for tool calls
                        if "tool_calls" in message:
                            if debug:
                                print("\nFound tool calls in response")
                            
                            tool_calls = message["tool_calls"]
                            
                            # Handle tool calls and update messages
                            messages = await self._handle_tool_calls(messages, tool_calls, debug)
                            
                            # Continue conversation with tool results
                            if debug:
                                print(f"\nContinuing conversation with updated messages: {json.dumps(messages, indent=2)}")
                            
                            # Make a new request with the updated messages
                            request["messages"] = messages
                            self.core._submit(json.dumps(request))
                            continue
                        
                        # Extract function call from content if present
                        function_match = re.search(r'<function-call>(.*?)</function-call>', content, re.DOTALL)
                        if function_match:
                            try:
                                function_data = json.loads(function_match.group(1).strip())
                                tool_calls = [{
                                    "id": str(uuid.uuid4()),
                                    "type": "function",
                                    "function": {
                                        "name": function_data["name"],
                                        "arguments": json.dumps(function_data["arguments"])
                                    }
                                }]
                                
                                # Handle tool calls and update messages
                                messages = await self._handle_tool_calls(messages, tool_calls, debug)
                                
                                # Continue conversation with tool results
                                if debug:
                                    print(f"\nContinuing conversation with updated messages: {json.dumps(messages, indent=2)}")
                                
                                # Make a new request with the updated messages
                                request["messages"] = messages
                                self.core._submit(json.dumps(request))
                                continue
                            except json.JSONDecodeError as e:
                                if debug:
                                    print(f"Error parsing function call JSON: {e}")
                        
                        # Then check for reasoning format
                        think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                        if think_match or message.get("reasoning"):
                            # Get reasoning either from think tags or reasoning field
                            reasoning = think_match.group(1).strip() if think_match else message.get("reasoning", "")
                            
                            # Get output - either after </think> or full content if no think tags
                            output = content[content.find("</think>") + 8:].strip() if think_match else content
                            
                            # Create ReasoningResponse
                            return ReasoningResponse(
                                _reasoning=reasoning,
                                _output=output,
                                _raw=response_data
                            )
                        
                        # Regular response if no reasoning found
                        return {
                            "text": content,
                            "raw_response": response_data
                        }
                    
                    # Handle final response
                    if "choices" in response_data:
                        message = response_data["choices"][0]["message"]
                        text = message.get("content")
                        
                        if debug:
                            print(f"\nFinal message: {json.dumps(message, indent=2)}")
                        
                        return {
                            "text": text or str(response_data),
                            "raw_response": response_data
                        }
                    
                    # Handle different response formats
                    if "candidates" in response_data:
                        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    elif "choices" in response_data:
                        text = response_data["choices"][0]["message"]["content"]
                    else:
                        text = response_data.get("text", str(response_data))
                    
                    if debug:
                        print(f"\nExtracted text: {text}")
                    
                    if not text:
                        if debug:
                            print("\nWarning: Extracted text is empty or None")
                        text = str(response_data)
                    
                    return {
                        "text": text,
                        "raw_response": response_data
                    }
                    
                except Exception as e:
                    if debug:
                        print(f"\nError parsing response: {e}")
                    return {
                        "text": str(response),
                        "raw_response": {"text": str(response)}
                    }
            await asyncio.sleep(0.1)

    async def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: str = "1024x1024",
        n: int = 1,
        response_format: str = "b64_json",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate image(s) via OpenAI-compatible v1 images endpoint.
        Returns the raw JSON dict from the provider.
        """
        base_url = self.config.base_url or "https://api.openai.com/v1"
        endpoint = f"{base_url}/images/generations"

        headers = (
            {"x-api-key": self.config.api_key}
            if self.config.provider == "anthropic"
            else {"Authorization": f"Bearer {self.config.api_key}"}
        )

        if model is None:
            if "/" in self.config.model:
                model = self.config.model.split("/")[-1]
            else:
                model = self.config.model

        request: Dict[str, Any] = {
            "_headers": headers,
            "_endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": response_format,
            **kwargs,
        }

        if self.debug:
            print(f"\nSending image generation request: {json.dumps(request, indent=2)[:1000]}...")

        self.core._submit(json.dumps(request))

        start = asyncio.get_event_loop().time()
        while True:
            if response := self.core._get_response():
                try:
                    return json.loads(response)
                except Exception:
                    return {"raw": response}
            if asyncio.get_event_loop().time() - start > self.config.timeout:
                raise TimeoutError("Image generation timed out")
            await asyncio.sleep(0.05)

    async def analyze_image(
        self,
        *,
        prompt: str,
        image_path: str,
        max_tokens: int = 128,
    ) -> Dict[str, Any]:
        """Analyze/describe an image with a text prompt via provider VLM APIs.

        Providers:
        - anthropic: messages API with image block
        - gemini: native generateContent with inline_data
        """
        # Derive short model name
        if '/' in self.config.model:
            model = self.config.model.split('/')[-1]
        else:
            model = self.config.model

        # Base64 encode image and guess MIME
        ext = os.path.splitext(image_path)[1].lower()
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(ext, "image/png")
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        if self.config.provider == "anthropic":
            headers = {"x-api-key": self.config.api_key}
            request: Dict[str, Any] = {
                "_headers": headers,
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {"type": "base64", "media_type": mime, "data": b64},
                            },
                        ],
                    }
                ],
                "max_tokens": max_tokens,
            }
        elif self.config.provider in ("gemini", "openai"):
            # Always force OpenAI-compatible chat/completions with explicit endpoint override
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ]

            # Choose provider-appropriate base URL, but allow explicit override via config.base_url
            default_base = (
                "https://api.openai.com/v1" if self.config.provider == "openai" else
                "https://generativelanguage.googleapis.com/v1beta/openai"
            )
            endpoint = f"{(self.config.base_url or default_base)}/chat/completions"
            request = {
                "_headers": {"Authorization": f"Bearer {self.config.api_key}"},
                "_endpoint": endpoint,
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
            }
        else:
            raise ValueError(f"analyze_image not supported for provider: {self.config.provider}")

        if self.debug:
            try:
                dbg = {k: v for k, v in request.items() if k != "_headers"}
                print(f"\nSending image analysis request: {json.dumps(dbg, indent=2)[:1000]}...")
            except Exception:
                pass
            if self.config.provider == "gemini":
                try:
                    print(f"Gemini analyze_image debug: prompt_len={len(prompt)}, b64_len={len(b64)}, mime={mime}")
                except Exception:
                    pass

        self.core._submit(json.dumps(request))

        start = asyncio.get_event_loop().time()
        while True:
            if response := self.core._get_response():
                try:
                    data = json.loads(response)
                except Exception:
                    return {"raw_response": response}

                if self.config.provider == "anthropic":
                    text = None
                    try:
                        text = data.get("content", [{}])[0].get("text")
                    except Exception:
                        pass
                    return {"text": text or str(data), "raw_response": data}
                elif self.config.provider == "gemini":
                    text = None
                    try:
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for p in parts:
                            if isinstance(p, dict) and "text" in p:
                                text = p["text"]
                                break
                    except Exception:
                        pass
                    return {"text": text or str(data), "raw_response": data}
            if asyncio.get_event_loop().time() - start > self.config.timeout:
                raise TimeoutError("Image analysis timed out")
            await asyncio.sleep(0.05)

    def register_image_tool(self) -> None:
        """Register a tool named 'generate_image' available to the model."""
        async def _image_tool(prompt: str, size: str = "1024x1024", n: int = 1) -> Dict[str, Any]:
            return await self.generate_image(prompt=prompt, size=size, n=n)

        self.register_tool(
            name="generate_image",
            func=_image_tool,
            description="Generate image(s) from a text prompt using the provider's image API.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Text prompt to generate images"},
                    "size": {"type": "string", "enum": ["256x256", "512x512", "1024x1024"]},
                    "n": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["prompt"],
                "additionalProperties": False,
            },
        )
    
    async def astream_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion responses"""
        # Extract model name after provider
        if '/' in self.config.model:
            parts = self.config.model.split('/')
            if self.config.provider in ['groq', 'openrouter', 'sambanova']:
                # Gateway providers: keep everything after provider (handles company/model)
                model = "/".join(parts[1:])
            else:
                # Foundation providers: just take model name after provider
                model = parts[1]
        else:
            model = self.config.model
        
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
                # Process any chunk we receive
                try:
                    # Try to parse as JSON first (for proper SSE format)
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
                    # Gemini uses OpenAI-compatible SSE via the /openai path; handle in the default branch.
                    else:
                        # Handle OpenAI-compatible providers (OpenAI, Groq, OpenRouter, SambaNova)
                        if "choices" in data:
                            choice = data["choices"][0]
                            if "delta" in choice:
                                delta = choice["delta"]
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]
                            
                            # Check for finish reason
                            if choice.get("finish_reason"):
                                break
                except json.JSONDecodeError:
                    # If not JSON, check for SSE format
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
                                        yield content
                            except json.JSONDecodeError:
                                # Raw SSE data that's not JSON
                                if data.strip():
                                    yield data
                    else:
                        # Raw text chunk - yield directly (this handles the case we're seeing)
                        yield chunk
            await asyncio.sleep(0.01)