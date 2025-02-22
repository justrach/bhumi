from dataclasses import dataclass
from typing import Optional, Dict, List, Union, AsyncIterator, Any, Callable, Type, get_type_hints
from .utils import async_retry
import bhumi.bhumi as _rust
import json
import asyncio
import os
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
        
        # Set default base URL if not provided
        if not self.base_url:
            if self.provider == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == "anthropic":
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1beta"
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
        try:
            # Try parsing as JSON first
            data = json.loads(response)
            return self.output_type.model_validate(data)
        except json.JSONDecodeError:
            # If not JSON, try to extract structured data from text
            return self._extract_structured_data(response)
    
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
        messages: List[Dict[str, str]],
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
        if self.tool_registry.get_definitions():
            tools = [tool.__dict__ for tool in self.tool_registry.get_definitions()]
            kwargs["tools"] = tools
            if debug:
                print(f"\nRegistered tools: {json.dumps(tools, indent=2)}")
            
        # Extract model name if it contains provider prefix
        model = self.config.model.split('/')[-1] if '/' in self.config.model else self.config.model
        
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
        request = {
            "_headers": headers,
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": kwargs.pop("max_tokens", self.config.max_tokens),
            **kwargs
        }
        
        # Handle Gemini-specific formatting
        if self.config.provider == "gemini":
            model_name = model.split('/')[-1]
            endpoint = f"{self.config.base_url}/models/{model_name}:generateContent"
            request["_endpoint"] = endpoint
            
            # Convert messages to Gemini format
            gemini_request = {
                "contents": [{
                    "role": "user",
                    "parts": [{
                        "text": messages[-1]["content"]
                    }]
                }]
            }
            
            # Add system instruction if present
            if len(messages) > 1 and messages[0]["role"] == "system":
                gemini_request["contents"].insert(0, {
                    "role": "system",
                    "parts": [{
                        "text": messages[0]["content"]
                    }]
                })
            
            # Add tools if registered
            if self.tool_registry.get_definitions():
                tools = [tool.__dict__ for tool in self.tool_registry.get_definitions()]
                gemini_request["tools"] = {
                    "function_declarations": [
                        {
                            "name": tool["function"]["name"],
                            "description": tool["function"]["description"],
                            "parameters": tool["function"]["parameters"]
                        } for tool in tools
                    ]
                }
                
                # Add tool config
                gemini_request["tool_config"] = {
                    "function_calling_config": {"mode": "auto"}
                }
            
            # Replace request with Gemini format
            request = {
                "_headers": {
                    "Authorization": f"Bearer {self.config.api_key}"
                },
                "_endpoint": endpoint,
                **gemini_request
            }
            
            if debug:
                print(f"\nGemini request: {json.dumps(request, indent=2)}")
        
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
                                
                                # Make a new request with the updated messages
                                request["contents"][-1]["parts"][0]["text"] = messages[-1]["content"]
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
                        print(f"Response that caused error: {response}")
                    return {
                        "text": str(response),
                        "raw_response": {"text": str(response)}
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