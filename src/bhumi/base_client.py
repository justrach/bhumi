from dataclasses import dataclass
from typing import Optional, Dict, List, Union, AsyncIterator, Any, Callable, Type, get_type_hints
from .utils import async_retry, extract_json_from_text, parse_json_loosely
from .json_compat import loads as json_loads, dumps as json_dumps, JSONDecodeError
import bhumi.bhumi as _rust
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
from .structured_outputs import (
    StructuredOutputParser, 
    ResponseFormat, 
    ParsedChatCompletion,
    pydantic_function_tool,
    pydantic_tool_schema,
    StructuredOutputError,
    LengthFinishReasonError,
    ContentFilterFinishReasonError
)

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
    debug_debug: bool = False
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
                    data = json_loads(data_str)
                    
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
                except JSONDecodeError:
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

# Backward compatibility alias - use new structured_outputs module instead
StructuredOutput = StructuredOutputParser

class BaseLLMClient:
    """Generic client for OpenAI-compatible APIs"""
    
    def __init__(
        self,
        config: LLMConfig,
        max_concurrent: int = 10,
        debug: bool = False,
        debug_debug: bool = False
    ):
        self.config = config
        self.max_concurrent = max_concurrent
        self.debug = debug or getattr(config, "debug", False) or (os.environ.get("BHUMI_DEBUG", "0") == "1")
        # Super-verbose debug (gates noisy logs)
        self.debug_debug = (
            debug_debug
            or getattr(config, "debug_debug", False)
            or (os.environ.get("BHUMI_DEBUG_DEBUG", "0") == "1")
        )
        
        # Create initial core
        self.core = _rust.BhumiCore(
            max_concurrent=max_concurrent,
            provider=config.provider or "generic",
            model=config.model,
            debug=self.debug,
            debug_debug=self.debug_debug,
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
        parameters: Dict[str, Any],
        *,
        aliases: Optional[Dict[str, str]] = None,
        on_unknown: str = "drop",
    ) -> None:
        """Register a new tool that can be called by the model"""
        self.tool_registry.register(
            name=name,
            func=func,
            description=description,
            parameters=parameters,
            aliases=aliases,
            on_unknown=on_unknown,
        )

    def set_structured_output(self, model: Type[BaseModel]) -> None:
        """
        Set up structured output handling with a Pydantic model.
        
        Note: This method is deprecated. Use the parse() method instead for better
        OpenAI/Anthropic compatibility.
        """
        self.structured_output = StructuredOutputParser(model)
        
        # Register a tool for structured output  
        self.register_tool(
            name="generate_structured_output",
            func=self._structured_output_handler,
            description=f"Generate structured output according to the schema: {model.__doc__}",
            parameters={"type": "object", "properties": model.model_json_schema().get("properties", {}), "required": model.model_json_schema().get("required", []), "additionalProperties": False}
        )
    
    async def _structured_output_handler(self, **kwargs) -> dict:
        """Handle structured output generation"""
        try:
            return self.structured_output.response_format(**kwargs).model_dump()
        except Exception as e:
            raise ValueError(f"Failed to create structured output: {e}")

    async def parse(
        self,
        messages: List[Dict[str, Any]],
        *,
        response_format: Type[Union[BaseModel, Any]],  # Support both Pydantic and Satya models
        stream: bool = False,
        debug: bool = False,
        timeout: Optional[float] = 30.0,  # Add timeout parameter
        **kwargs
    ) -> Union[ParsedChatCompletion, AsyncIterator[str]]:
        """
        Create a completion with automatic parsing of structured outputs.
        
        Similar to OpenAI's client.chat.completions.parse() method.
        Automatically converts Pydantic or Satya models to JSON schema and parses
        the response back into the specified model with high-performance validation.
        
        Args:
            messages: List of messages for the conversation
            response_format: Pydantic BaseModel or Satya Model class to parse response into
            stream: Whether to stream the response (not supported for parsing)
            debug: Enable debug logging
            **kwargs: Additional arguments passed to completion()
            
        Returns:
            ParsedChatCompletion with validated structured content
            
        Raises:
            ValueError: If streaming is requested (not supported)
            LengthFinishReasonError: If completion finished due to length limits
            ContentFilterFinishReasonError: If completion finished due to content filtering
            StructuredOutputError: If parsing fails
            
        Note:
            Satya models provide high-performance Rust-powered validation and are
            recommended for production workloads requiring fast structured outputs.
        """
        if stream:
            raise ValueError("Streaming is not supported with parse() method. Use completion() with stream=True instead.")
        
        # Create response format for the model
        response_format_dict = ResponseFormat.from_model(response_format)
        
        # Add response_format to kwargs
        kwargs["response_format"] = response_format_dict
        
        # Get completion response with timeout
        import asyncio
        try:
            response = await asyncio.wait_for(
                self.completion(messages, stream=False, debug=debug, **kwargs),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise ValueError(f"API call timed out after {timeout} seconds. Try increasing timeout for complex schemas or large models.")
        except Exception as e:
            raise ValueError(f"API call failed: {e}")
        
        # Parse using structured output parser
        parser = StructuredOutputParser(response_format)
        
        # Handle different response types
        if isinstance(response, ReasoningResponse):
            # For reasoning responses, create a mock API response format
            mock_response = {
                "id": "reasoning-" + str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(asyncio.get_event_loop().time()),
                "model": self.config.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response._output
                    },
                    "finish_reason": "stop"
                }]
            }
        elif isinstance(response, dict) and "raw_response" in response:
            mock_response = response["raw_response"]
        else:
            # Create mock response from simple dict response
            content = response.get("text", str(response)) if isinstance(response, dict) else str(response)
            mock_response = {
                "id": "completion-" + str(uuid.uuid4()),
                "object": "chat.completion", 
                "created": int(asyncio.get_event_loop().time()),
                "model": self.config.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }]
            }
        
        return parser.parse_response(mock_response)

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
            if self.debug_debug:
                print(f"\nProcessing tool call: {json_dumps(tool_call)}")
            
            # Create ToolCall object
            call = ToolCall(
                id=tool_call.get("id", str(uuid.uuid4())),
                type=tool_call["type"],
                function=tool_call["function"]
            )
            
            try:
                # Execute the tool
                if self.debug_debug:
                    print(f"\nExecuting tool: {call.function['name']}")
                    print(f"Arguments: {call.function['arguments']}")
                
                result = await self.tool_registry.execute_tool(call)
                
                if self.debug_debug:
                    print(f"Tool execution result: {result}")
                
                # Add tool result to messages
                tool_message = {
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": call.id
                }
                
                messages.append(tool_message)
                
                if self.debug_debug:
                    print(f"Added tool message: {json_dumps(tool_message)}")
                    
            except Exception as e:
                if self.debug_debug:
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
            if self.debug_debug:
                print(f"\nRegistered tools ({self.config.provider}): {json_dumps(tools)}")
            
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
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
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
            # GPT-5 models expect 'max_completion_tokens' instead of 'max_tokens'
            try:
                is_gpt5 = bool(re.search(r"(?:^|/)gpt-5", model))
            except Exception:
                is_gpt5 = isinstance(model, str) and model.startswith("gpt-5")
            token_field = "max_completion_tokens" if is_gpt5 else "max_tokens"
            request[token_field] = req_max_tokens
        
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

        if self.debug_debug:
            print(f"\nSending request: {json_dumps(request)}")
        
        # Submit request
        self.core._submit(json_dumps(request))
        
        while True:
            if response := self.core._get_response():
                try:
                    if debug:
                        print(f"\nRaw response: {response}")
                    
                    response_data = json_loads(response)
                    
                    # Anthropic non-streaming AFC: detect tool_use blocks, execute, and continue
                    if (
                        (self.config.provider == "anthropic")
                        and isinstance(response_data, dict)
                        and isinstance(response_data.get("content"), list)
                    ):
                        content_blocks = response_data.get("content", [])
                        tool_use_blocks = [b for b in content_blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
                        if tool_use_blocks:
                            # Append the assistant tool_use message as-is
                            messages.append({
                                "role": "assistant",
                                "content": content_blocks,
                            })

                            # Execute tools and build tool_result blocks
                            tool_results: List[Dict[str, Any]] = []
                            for tub in tool_use_blocks:
                                call = ToolCall(
                                    id=tub.get("id") or str(uuid.uuid4()),
                                    type="function",
                                    function={
                                        "name": tub.get("name"),
                                        "arguments": tub.get("input", {}),
                                    },
                                )
                                try:
                                    result = await self.tool_registry.execute_tool(call)
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": call.id,
                                        "content": str(result),
                                    })
                                except Exception as e:
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": call.id,
                                        "content": f"Error: {e}",
                                    })

                            # Continue conversation with tool results as user blocks
                            messages.append({
                                "role": "user",
                                "content": tool_results,
                            })

                            # Re-normalize anthropic block schema and resubmit
                            next_request = dict(request)
                            norm_msgs: List[Dict[str, Any]] = []
                            for m in messages:
                                c = m.get("content", "")
                                if isinstance(c, str):
                                    c = [{"type": "text", "text": c}]
                                norm_msgs.append({"role": m.get("role", "user"), "content": c})
                            next_request["messages"] = norm_msgs
                            if self.debug_debug:
                                try:
                                    print(f"\n[anthropic][non-stream AFC] resubmitting with tool_results: {json_dumps(tool_results)}")
                                except Exception:
                                    pass
                            self.core._submit(json_dumps(next_request))
                            continue

                    # Check for tool calls in response
                    if "tool_calls" in response_data.get("choices", [{}])[0].get("message", {}):
                        if debug:
                            print("\nFound tool calls in response")
                        
                        tool_calls = response_data["choices"][0]["message"]["tool_calls"]
                        
                        # Handle tool calls and update messages
                        messages = await self._handle_tool_calls(messages, tool_calls, debug)
                        
                        # Continue conversation with tool results
                        if self.debug_debug:
                            print(f"\nContinuing conversation with updated messages: {json_dumps(messages)}")
                        
                        # Make a new request with the updated messages
                        request["messages"] = messages
                        self.core._submit(json_dumps(request))
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
                                if self.debug_debug:
                                    print(f"\nContinuing conversation with updated messages: {json_dumps(messages)}")
                                
                                # Make a new request with the updated messages (OpenAI-compatible continuation)
                                request["messages"] = messages
                                self.core._submit(json_dumps(request))
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
                            if self.debug_debug:
                                print(f"\nContinuing conversation with updated messages: {json_dumps(messages)}")
                            
                            # Make a new request with the updated messages
                            request["messages"] = messages
                            self.core._submit(json_dumps(request))
                            continue
                        
                        # Extract function call from content if present
                        function_match = re.search(r'<function-call>(.*?)</function-call>', content, re.DOTALL)
                        if function_match:
                            try:
                                function_data = json_loads(function_match.group(1).strip())
                                tool_calls = [{
                                    "id": str(uuid.uuid4()),
                                    "type": "function",
                                    "function": {
                                        "name": function_data["name"],
                                        "arguments": json_dumps(function_data["arguments"])
                                    }
                                }]
                                
                                # Handle tool calls and update messages
                                messages = await self._handle_tool_calls(messages, tool_calls, debug)
                                
                                # Continue conversation with tool results
                                if debug:
                                    print(f"\nContinuing conversation with updated messages: {json_dumps(messages)}")
                                
                                # Make a new request with the updated messages
                                request["messages"] = messages
                                self.core._submit(json_dumps(request))
                                continue
                            except JSONDecodeError as e:
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
                        
                        if self.debug_debug:
                            print(f"\nFinal message: {json_dumps(message)}")
                        
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

        if self.debug_debug:
            try:
                print(f"\nSending image generation request: {json_dumps(request)[:1000]}...")
            except Exception:
                pass

        self.core._submit(json_dumps(request))

        start = asyncio.get_event_loop().time()
        while True:
            if response := self.core._get_response():
                try:
                    return json_loads(response)
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
            # Determine token field for GPT-5
            try:
                is_gpt5_img = bool(re.search(r"(?:^|/)gpt-5", model))
            except Exception:
                is_gpt5_img = isinstance(model, str) and model.startswith("gpt-5")
            token_field_img = "max_completion_tokens" if is_gpt5_img else "max_tokens"
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
                token_field_img: max_tokens,
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
            # Determine token field for GPT-5
            try:
                is_gpt5_img2 = bool(re.search(r"(?:^|/)gpt-5", model))
            except Exception:
                is_gpt5_img2 = isinstance(model, str) and model.startswith("gpt-5")
            token_field_img2 = "max_completion_tokens" if is_gpt5_img2 else "max_tokens"
            request = {
                "_headers": {"Authorization": f"Bearer {self.config.api_key}"},
                "_endpoint": endpoint,
                "model": model,
                "messages": messages,
                token_field_img2: max_tokens,
            }
        else:
            raise ValueError(f"analyze_image not supported for provider: {self.config.provider}")

        if self.debug_debug:
            try:
                dbg = {k: v for k, v in request.items() if k != "_headers"}
                print(f"\nSending image analysis request: {json_dumps(dbg)[:1000]}...")
            except Exception:
                pass
        if self.config.provider == "gemini":
            try:
                print(f"Gemini analyze_image debug: prompt_len={len(prompt)}, b64_len={len(b64)}, mime={mime}")
            except Exception:
                pass

        self.core._submit(json_dumps(request))

        start = asyncio.get_event_loop().time()
        while True:
            if response := self.core._get_response():
                try:
                    data = json_loads(response)
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
        
        # Prepare headers consistent with non-streaming path
        if self.config.provider == "anthropic":
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
            }
        else:
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        # Prepare base streaming request
        # Determine token field based on model (GPT-5 uses 'max_completion_tokens')
        try:
            is_gpt5_stream = bool(re.search(r"(?:^|/)gpt-5", model))
        except Exception:
            is_gpt5_stream = isinstance(model, str) and model.startswith("gpt-5")
        token_field_stream = "max_completion_tokens" if is_gpt5_stream else "max_tokens"
        req_max_tokens_stream = kwargs.pop("max_tokens", 1024)
        request = {
            "model": model,
            "messages": messages,
            "stream": True,
            "_headers": headers,
            token_field_stream: req_max_tokens_stream,
            **kwargs
        }

        # Normalize Anthropics messages to block schema (same as non-streaming)
        if self.config.provider == "anthropic":
            norm_msgs: List[Dict[str, Any]] = []
            for m in request.get("messages", []):
                content = m.get("content", "")
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                norm_msgs.append({"role": m.get("role", "user"), "content": content})
            request["messages"] = norm_msgs
        
        # Add tools if any are registered
        public_tools = self.tool_registry.get_public_definitions()
        if public_tools:
            if self.config.provider == "anthropic":
                request["tools"] = self.tool_registry.get_anthropic_definitions()
            else:
                request["tools"] = public_tools
        
        if self.debug:
            print(f"Sending streaming request for {self.config.provider}")
        
        # Local copy of messages that we will mutate when handling tool calls
        running_messages = list(messages)

        # Function-call accumulation for OpenAI-compatible streaming
        tool_accum: Dict[int, Dict[str, Any]] = {}
        # Anthropic tool_use accumulation during streaming
        anthropic_tools: Dict[int, Dict[str, Any]] = {}
        # Debug state
        round_idx = 1
        chunk_count = 0

        if self.debug:
            try:
                print(f"[bhumi] submit stream round={round_idx} provider={self.config.provider} model={model}")
                print(f"[bhumi] tools_registered={bool(public_tools)} timeout={self.config.timeout}")
            except Exception:
                pass
        self.core._submit(json_dumps(request))
        start = asyncio.get_event_loop().time()
        
        while True:
            chunk = self.core._get_stream_chunk()
            if chunk == "[DONE]":
                # Try to harvest a final non-stream response (common after tool-calls).
                # Poll briefly because the core may enqueue it slightly after [DONE].
                try:
                    get_resp = getattr(self.core, "_get_response", None)
                except Exception:
                    get_resp = None
                if callable(get_resp):
                    harvest_start = asyncio.get_event_loop().time()
                    while True:
                        resp = get_resp()
                        if resp:
                            try:
                                data = json_loads(resp)
                                text_out = None
                                if isinstance(data, dict) and "choices" in data:
                                    text_out = (
                                        data.get("choices", [{}])[0]
                                        .get("message", {})
                                        .get("content")
                                    )
                                elif isinstance(data, dict) and "candidates" in data:
                                    try:
                                        text_out = (
                                            data["candidates"][0]
                                            .get("content", {})
                                            .get("parts", [{}])[0]
                                            .get("text")
                                        )
                                    except Exception:
                                        text_out = None
                                if text_out:
                                    if self.debug:
                                        print("[bhumi] harvested final text after [DONE]")
                                    yield text_out
                                    break
                                else:
                                    # Unknown dict payload; yield raw
                                    yield json_dumps(data)
                                    break
                            except Exception:
                                # Non-JSON payload; yield raw response text
                                yield str(resp)
                                break
                        # Timeout after ~2.0s of waiting
                        if asyncio.get_event_loop().time() - harvest_start > 2.0:
                            break
                        await asyncio.sleep(0.01)
                break
            if chunk:
                # Process any chunk we receive
                try:
                    # Try to parse as JSON first (for proper SSE format)
                    data = json_loads(chunk)
                    # Surface provider error bodies that were forwarded via stream chunks
                    if isinstance(data, dict) and data.get("error"):
                        # OpenAI-style error object: {"error": {"message": "...", ...}}
                        err = data.get("error")
                        if isinstance(err, dict):
                            msg = err.get("message") or json_dumps(err)
                        else:
                            msg = str(err)
                        raise RuntimeError(f"Provider error during streaming: {msg}")
                    
                    # If provider returns a JSON primitive (string/number), yield it directly
                    # This happens for some providers when streaming simple tokens like digits.
                    if not isinstance(data, dict):
                        text = str(data)
                        if text:
                            yield text
                        continue
                        
                    if self.config.provider == "anthropic":
                        # Handle Anthropic's SSE format
                        evt_type = data.get("type")
                        # Some providers may return a full non-SSE JSON message as a single chunk
                        # e.g., {"type":"message","content":[{"type":"text","text":"..."}], ...}
                        if not evt_type and isinstance(data, dict) and data.get("content"):
                            try:
                                parts = data.get("content") or []
                                texts = []
                                for p in parts:
                                    if isinstance(p, dict) and p.get("type") == "text":
                                        t = p.get("text")
                                        if t:
                                            texts.append(t)
                                final_text = "".join(texts)
                                if final_text:
                                    yield final_text
                                    break
                            except Exception:
                                pass
                        if evt_type == "content_block_start":
                            cb = data.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                idx = data.get("index", 0)
                                anthropic_tools[idx] = {
                                    "id": cb.get("id") or str(uuid.uuid4()),
                                    "type": "function",
                                    "function": {"name": cb.get("name", ""), "arguments": ""},
                                }
                        elif evt_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text_piece = delta.get("text", "")
                                if text_piece:
                                    if self.debug:
                                        chunk_count += 1
                                    yield text_piece
                            elif delta.get("type") == "input_json_delta":
                                idx = data.get("index", 0)
                                acc = anthropic_tools.setdefault(idx, {"function": {"arguments": ""}})
                                acc_fn = acc.setdefault("function", {"name": "", "arguments": ""})
                                acc_fn["arguments"] += delta.get("partial_json", "")
                        elif evt_type == "message_stop":
                            # If we accumulated tool_use calls, execute and continue conversation
                            if anthropic_tools:
                                tool_calls_list = []
                                for idx in sorted(anthropic_tools.keys()):
                                    tc = anthropic_tools[idx]
                                    # Fallback to empty JSON if arguments are missing
                                    if not tc.get("function", {}).get("arguments"):
                                        tc["function"]["arguments"] = "{}"
                                    tool_calls_list.append(tc)

                                # Execute tools and build Anthropic tool_result message
                                tool_results = []
                                for tc in tool_calls_list:
                                    call = ToolCall(
                                        id=tc.get("id") or str(uuid.uuid4()),
                                        type=tc.get("type", "function"),
                                        function=tc.get("function", {}),
                                    )
                                    try:
                                        result = await self.tool_registry.execute_tool(call)
                                        tool_results.append({
                                            "type": "tool_result",
                                            "tool_use_id": call.id,
                                            "content": str(result),
                                        })
                                    except Exception as e:
                                        tool_results.append({
                                            "type": "tool_result",
                                            "tool_use_id": call.id,
                                            "content": f"Error: {e}",
                                        })

                                # Append as a user message with tool_result blocks
                                running_messages.append({
                                    "role": "user",
                                    "content": tool_results,
                                })

                                # Reset accumulators and continue with updated messages
                                anthropic_tools = {}
                                next_request = dict(request)
                                # Re-normalize anthropic message blocks for continuation
                                norm_msgs: List[Dict[str, Any]] = []
                                for m in running_messages:
                                    content = m.get("content", "")
                                    if isinstance(content, str):
                                        content = [{"type": "text", "text": content}]
                                    norm_msgs.append({"role": m.get("role", "user"), "content": content})
                                next_request["messages"] = norm_msgs
                                self.core._submit(json_dumps(next_request))
                                continue
                            else:
                                break
                    # Gemini uses OpenAI-compatible SSE via the /openai path; handle in the default branch.
                    else:
                        # Handle OpenAI-compatible providers (OpenAI, Groq, OpenRouter, SambaNova)
                        if "choices" in data:
                            choice = data["choices"][0]
                            if "delta" in choice:
                                delta = choice["delta"]
                                # 1) Content deltas
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]
                                # 2) Tool call deltas
                                if "tool_calls" in delta and isinstance(delta["tool_calls"], list):
                                    for item in delta["tool_calls"]:
                                        idx = item.get("index", 0)
                                        acc = tool_accum.setdefault(
                                            idx,
                                            {
                                                "id": item.get("id"),
                                                "type": item.get("type", "function"),
                                                "function": {"name": "", "arguments": ""},
                                            },
                                        )
                                        fn = item.get("function") or {}
                                        if "name" in fn and fn["name"]:
                                            acc["function"]["name"] = fn["name"]
                                        if "arguments" in fn and fn["arguments"]:
                                            # Accumulate JSON argument string fragments
                                            acc["function"]["arguments"] += fn["arguments"]
                            else:
                                # Non-delta JSON chunk (provider sent final full message mid-stream)
                                msg = choice.get("message", {})
                                # If this is a tool_call result, let finish_reason logic handle it below
                                if isinstance(msg, dict) and msg.get("content"):
                                    yield msg.get("content")
                                    break

                            # Check for finish reason
                            finish_reason = choice.get("finish_reason")
                            if self.debug:
                                try:
                                    print(
                                        f"DEBUG stream: finish_reason={finish_reason} accum_keys={list(tool_accum.keys())} accum={json_dumps(tool_accum)}"
                                    )
                                except Exception:
                                    print(
                                        f"DEBUG stream: finish_reason={finish_reason} accum_keys={list(tool_accum.keys())}"
                                    )
                            if finish_reason == "tool_calls":
                                # Execute accumulated tools, then continue streaming with updated messages
                                tool_calls_list = []
                                for idx in sorted(tool_accum.keys()):
                                    tc = tool_accum[idx]
                                    tool_calls_list.append(
                                        {
                                            "id": tc.get("id") or str(uuid.uuid4()),
                                            "type": tc.get("type", "function"),
                                            "function": {
                                                "name": tc.get("function", {}).get("name"),
                                                "arguments": tc.get("function", {}).get("arguments", "{}"),
                                            },
                                        }
                                    )

                                # Handle tool calls (executes and appends tool results)
                                running_messages = await self._handle_tool_calls(
                                    running_messages, tool_calls_list, debug=self.debug
                                )

                                # Reset accumulators for next round
                                tool_accum = {}

                                # Continue conversation by resubmitting with updated messages
                                next_request = dict(request)
                                next_request["messages"] = running_messages
                                # Force final answer phase: do not allow further tool calls
                                # Keep tools present (some providers require tools when tool_choice is provided)
                                next_request["tool_choice"] = "none"
                                # For OpenAI, request a non-stream final round to ensure we get the full answer
                                # without requiring environment flags.
                                if self.config.provider in ("openai",):
                                    next_request["stream"] = False
                                    # Submit and harvest a single final response immediately
                                    self.core._submit(json_dumps(next_request))
                                    harvest_start = asyncio.get_event_loop().time()
                                    while True:
                                        _gr = getattr(self.core, "_get_response", None)
                                        resp = _gr() if callable(_gr) else None
                                        if resp:
                                            try:
                                                data = json_loads(resp)
                                                text = None
                                                if isinstance(data, dict) and "choices" in data:
                                                    text = (
                                                        data.get("choices", [{}])[0]
                                                        .get("message", {})
                                                        .get("content")
                                                    )
                                                if text:
                                                    yield text
                                                else:
                                                    # Unknown dict payload; yield raw
                                                    yield json_dumps(data)
                                                break
                                            except Exception:
                                                # Non-JSON payload; yield raw response text
                                                yield str(resp)
                                                break
                                        if asyncio.get_event_loop().time() - harvest_start > self.config.timeout:
                                            raise TimeoutError("Final non-stream round timed out")
                                        await asyncio.sleep(0.01)
                                    break

                                # Optional hybrid fallback for providers with unstable multi-round streams
                                # Enable by setting BHUMI_HYBRID_TOOLS=1
                                use_hybrid = os.environ.get("BHUMI_HYBRID_TOOLS", "0") == "1"
                                if use_hybrid and self.config.provider in ("openai",):
                                    if self.debug:
                                        print("[bhumi] tool_calls finish -> using hybrid non-stream round")
                                    next_request["stream"] = False
                                    self.core._submit(json_dumps(next_request))
                                    # Read single final response, yield its text, and finish
                                    hybrid_start = asyncio.get_event_loop().time()
                                    while True:
                                        # Guard for cores that may not implement _get_response (e.g., MockCore)
                                        _gr = getattr(self.core, "_get_response", None)
                                        resp = _gr() if callable(_gr) else None
                                        if resp:
                                            try:
                                                data = json_loads(resp)
                                                text = None
                                                if isinstance(data, dict) and "choices" in data:
                                                    text = (
                                                        data.get("choices", [{}])[0]
                                                        .get("message", {})
                                                        .get("content")
                                                    )
                                                if text:
                                                    yield text
                                                break
                                            except Exception:
                                                yield str(resp)
                                                break
                                        if asyncio.get_event_loop().time() - hybrid_start > self.config.timeout:
                                            raise TimeoutError("Hybrid tools round timed out")
                                        await asyncio.sleep(0.01)
                                    break
                                else:
                                    # Continue streaming normally (AFC-style)
                                    round_idx += 1
                                    if self.debug:
                                        print(f"[bhumi] tool_calls finish -> submit stream round={round_idx}")
                                    self.core._submit(json_dumps(next_request))
                                    # Continue loop to process next streaming round
                                    continue
                            elif finish_reason:
                                break
                except JSONDecodeError:
                    # If not JSON, check for SSE format
                    if chunk.startswith("data: "):
                        data = chunk.removeprefix("data: ")
                        if data != "[DONE]":
                            try:
                                parsed = json_loads(data)
                                if isinstance(parsed, dict) and "choices" in parsed:
                                    content = (parsed.get("choices", [{}])[0]
                                             .get("delta", {})
                                             .get("content"))
                                    if content:
                                        if self.debug:
                                            chunk_count += 1
                                        yield content
                            except JSONDecodeError:
                                # Raw SSE data that's not JSON
                                if data.strip():
                                    if self.debug:
                                        chunk_count += 1
                                    yield data
                    else:
                        # Raw text chunk - yield directly (this handles the case we're seeing)
                        if self.debug:
                            chunk_count += 1
                        yield chunk
            # Check for any immediate non-stream error/response from core
            # Some test cores (e.g., MockCore) do not implement _get_response; guard accordingly.
            get_resp = None
            try:
                get_resp = getattr(self.core, "_get_response", None)
            except Exception:
                get_resp = None
            if callable(get_resp):
                resp = get_resp()
                if resp:
                    try:
                        data = json_loads(resp)
                        # Surface provider errors early
                        if isinstance(data, dict) and data.get("error"):
                            raise RuntimeError(f"Provider error during streaming: {data['error']}")
                        # If it's a normal response, try to extract final text and yield it
                        text_out = None
                        if isinstance(data, dict):
                            if "choices" in data:
                                text_out = (
                                    data.get("choices", [{}])[0]
                                    .get("message", {})
                                    .get("content")
                                )
                            elif "candidates" in data:
                                try:
                                    text_out = (
                                        data["candidates"][0]
                                        .get("content", {})
                                        .get("parts", [{}])[0]
                                        .get("text")
                                    )
                                except Exception:
                                    text_out = None
                        if text_out:
                            if self.debug:
                                print(
                                    f"[bhumi] non-stream response mid-stream -> yielding final text; chunks={chunk_count}"
                                )
                            yield text_out
                        else:
                            if self.debug:
                                print(
                                    f"[bhumi] non-stream response mid-stream with no extractable text; chunks={chunk_count}"
                                )
                        break
                    except Exception:
                        # Unknown payload; yield raw response text and end
                        if self.debug:
                            print("[bhumi] non-stream response mid-stream (unknown format); yielding raw text")
                        yield str(resp)
                        break

            # Timeout handling for stuck streams
            now = asyncio.get_event_loop().time()
            if now - start > self.config.timeout:
                raise TimeoutError(f"Streaming timed out after {self.config.timeout} seconds for provider {self.config.provider}")
            await asyncio.sleep(0.01)
