"""
Structured outputs implementation following OpenAI and Anthropic patterns.

This module provides:
- JSON schema generation from Pydantic and Satya models
- Response format configuration for structured outputs
- Parsed completion types with automatic validation
- Tool definition helpers for structured tool calls
- High-performance validation with Satya integration
"""

from __future__ import annotations

import json
import inspect
from typing import Type, TypeVar, Dict, Any, Optional, Union, List, get_type_hints
from dataclasses import dataclass

# Import Pydantic (always available)
from pydantic import BaseModel, ValidationError, create_model

# Import Satya (optional but recommended for performance)
try:
    from satya import Model as SatyaModel, Field as SatyaField, ValidationError as SatyaValidationError
    SATYA_AVAILABLE = True
except ImportError:
    SATYA_AVAILABLE = False
    SatyaModel = None
    SatyaField = None
    SatyaValidationError = None

# Type variables for both model types
T = TypeVar('T', bound=Union[BaseModel, 'SatyaModel'])
PydanticModel = TypeVar('PydanticModel', bound=BaseModel)
if SATYA_AVAILABLE:
    SatyaModelType = TypeVar('SatyaModelType', bound=SatyaModel)


class StructuredOutputError(Exception):
    """Base exception for structured output errors"""
    pass


class SchemaValidationError(StructuredOutputError):
    """Raised when response doesn't match expected schema"""
    pass


class LengthFinishReasonError(StructuredOutputError):
    """Raised when completion finishes due to length limits"""
    pass


class ContentFilterFinishReasonError(StructuredOutputError):
    """Raised when completion finishes due to content filtering"""
    pass


@dataclass
class ParsedMessage:
    """Represents a parsed message with structured content"""
    content: Optional[str] = None
    parsed: Optional[Union[BaseModel, 'SatyaModel']] = None
    refusal: Optional[str] = None
    role: str = "assistant"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def __bool__(self) -> bool:
        """Returns True if parsing was successful"""
        return self.parsed is not None


@dataclass
class ParsedChoice:
    """Represents a parsed choice from the completion response"""
    message: ParsedMessage
    index: int = 0
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


@dataclass 
class ParsedChatCompletion:
    """
    Represents a parsed chat completion response, similar to OpenAI's ParsedChatCompletion.
    Contains the original response plus parsed structured data.
    """
    id: str
    choices: List[ParsedChoice]
    created: int
    model: str
    object: str = "chat.completion"
    system_fingerprint: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    
    @property
    def parsed(self) -> Optional[Union[BaseModel, 'SatyaModel']]:
        """Get the first parsed result for convenience"""
        if self.choices and self.choices[0].message.parsed:
            return self.choices[0].message.parsed
        return None


def _is_pydantic_model(model_class: Type) -> bool:
    """Check if a class is a Pydantic model"""
    return (
        inspect.isclass(model_class) and 
        issubclass(model_class, BaseModel)
    )


def _is_satya_model(model_class: Type) -> bool:
    """Check if a class is a Satya model"""
    return (
        SATYA_AVAILABLE and 
        inspect.isclass(model_class) and 
        issubclass(model_class, SatyaModel)
    )


def _get_model_schema(model_class: Type) -> Dict[str, Any]:
    """Get JSON schema from either Pydantic or Satya model"""
    if _is_pydantic_model(model_class):
        return model_class.model_json_schema()
    elif _is_satya_model(model_class):
        # Use Satya v0.3.6's built-in OpenAI-compatible schema generation
        try:
            return model_class.model_json_schema()
        except AttributeError:
            # Fallback for older Satya versions
            return model_class.json_schema()
    else:
        raise ValueError(f"Unsupported model type: {model_class}. Must be Pydantic BaseModel or Satya Model.")



def _validate_with_model(model_class: Type, data: Dict[str, Any]) -> Union[BaseModel, 'SatyaModel']:
    """Validate data with either Pydantic or Satya model"""
    if _is_pydantic_model(model_class):
        return model_class.model_validate(data)
    elif _is_satya_model(model_class):
        # Satya v0.3 validation - use model_validate (Pydantic-compatible API)
        try:
            # Use the Pydantic-compatible method first
            if hasattr(model_class, 'model_validate'):
                return model_class.model_validate(data)
            else:
                # Fallback to direct instantiation with validation
                return model_class(**data)
        except Exception as e:
            # If Satya validation fails, provide detailed error
            if SATYA_AVAILABLE and isinstance(e, SatyaValidationError):
                raise ValueError(f"Satya validation failed: {e}")
            else:
                raise ValueError(f"Satya model validation failed for {model_class.__name__}: {e}")
    else:
        raise ValueError(f"Unsupported model type: {model_class}. Must be Pydantic BaseModel or Satya Model.")


def pydantic_function_tool(model: Type[Union[BaseModel, 'SatyaModel']], *, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a Pydantic or Satya model to a function tool definition with strict JSON schema.
    Similar to OpenAI's pydantic_function_tool helper.
    
    Args:
        model: Pydantic BaseModel or Satya Model class to convert
        name: Optional name for the tool (defaults to model name)
        description: Optional description (defaults to model docstring)
    
    Returns:
        Tool definition dict compatible with OpenAI-style function calling
    """
    schema = _get_model_schema(model)
    
    return {
        "type": "function",
        "function": {
            "name": name or model.__name__.lower(),
            "description": description or model.__doc__ or f"Execute {model.__name__}",
            "parameters": {
                "type": "object", 
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
                "additionalProperties": False
            },
            "strict": True
        }
    }


def pydantic_tool_schema(model: Type[Union[BaseModel, 'SatyaModel']]) -> Dict[str, Any]:
    """
    Convert Pydantic or Satya model to Anthropic-style tool schema.
    
    Args:
        model: Pydantic BaseModel or Satya Model class to convert
        
    Returns:
        Tool schema dict compatible with Anthropic's tool calling format
    """
    schema = _get_model_schema(model)
    
    return {
        "name": model.__name__.lower(),
        "description": model.__doc__ or f"Use the {model.__name__} tool",
        "input_schema": {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
            "additionalProperties": False
        }
    }


class ResponseFormat:
    """Helper class for creating response format specifications"""
    
    @staticmethod
    def json_object() -> Dict[str, str]:
        """Create a JSON object response format"""
        return {"type": "json_object"}
    
    @staticmethod 
    def json_schema(schema: Dict[str, Any], *, name: str, description: Optional[str] = None, strict: bool = True) -> Dict[str, Any]:
        """Create a JSON schema response format"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": name,
                "description": description or f"Schema for {name}",
                "schema": schema,
                "strict": strict
            }
        }
    
    @staticmethod
    def from_model(model: Type[Union[BaseModel, 'SatyaModel']], *, name: Optional[str] = None, strict: bool = False) -> Dict[str, Any]:
        """Create response format from Pydantic or Satya model"""
        schema = _get_model_schema(model)
        model_name = name or model.__name__.lower()
        
        return ResponseFormat.json_schema(
            schema=schema,
            name=model_name, 
            description=model.__doc__,
            strict=strict
        )


class StructuredOutputParser:
    """
    Parser for handling structured outputs with automatic validation.
    Follows patterns similar to OpenAI's client.chat.completions.parse() method.
    Supports both Pydantic and Satya models for high-performance validation.
    """
    
    def __init__(self, response_format: Type[Union[BaseModel, 'SatyaModel']]):
        self.response_format = response_format
        self._schema = _get_model_schema(response_format)
        
        # For Satya models, pre-create validator for performance
        self._satya_validator = None
        if _is_satya_model(response_format):
            self._satya_validator = response_format.validator()
            self._satya_validator.set_batch_size(1)  # Single item validation
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from various response formats"""
        content = content.strip()
        
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        import re
        
        # Look for ```json blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Look for first balanced JSON object
        for i, char in enumerate(content):
            if char == '{':
                depth = 0
                for j in range(i, len(content)):
                    if content[j] == '{':
                        depth += 1
                    elif content[j] == '}':
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(content[i:j+1])
                            except json.JSONDecodeError:
                                break
                break
        
        # Look for first balanced JSON array  
        for i, char in enumerate(content):
            if char == '[':
                depth = 0
                for j in range(i, len(content)):
                    if content[j] == '[':
                        depth += 1
                    elif content[j] == ']':
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(content[i:j+1])
                            except json.JSONDecodeError:
                                break
                break
        
        raise SchemaValidationError("No valid JSON found in response content")
    
    def parse_response(self, response_data: Dict[str, Any]) -> ParsedChatCompletion:
        """
        Parse a completion response into a ParsedChatCompletion with validated structured data.
        
        Args:
            response_data: Raw response data from the API
            
        Returns:
            ParsedChatCompletion with validated structured content
            
        Raises:
            LengthFinishReasonError: If completion finished due to length limits
            ContentFilterFinishReasonError: If completion finished due to content filtering
            SchemaValidationError: If response doesn't match expected schema
        """
        # Check for problematic finish reasons
        choices = response_data.get("choices", [])
        if choices:
            finish_reason = choices[0].get("finish_reason")
            if finish_reason == "length":
                raise LengthFinishReasonError("Completion finished due to length limits")
            elif finish_reason == "content_filter":
                raise ContentFilterFinishReasonError("Completion finished due to content filtering")
        
        parsed_choices = []
        
        for i, choice in enumerate(choices):
            message = choice.get("message", {})
            content = message.get("content", "")
            refusal = message.get("refusal")
            
            parsed_obj = None
            if content and not refusal:
                try:
                    # Extract and validate JSON
                    json_data = self._extract_json_from_response(content)
                    parsed_obj = _validate_with_model(self.response_format, json_data)
                except (json.JSONDecodeError, ValidationError, SchemaValidationError) as e:
                    # Also catch Satya validation errors if available
                    if SATYA_AVAILABLE and isinstance(e, SatyaValidationError):
                        parsed_obj = None
                    else:
                        # Don't raise here - let user handle validation errors gracefully
                        parsed_obj = None
                except Exception as e:
                    # Catch any other validation errors
                    parsed_obj = None
            
            parsed_message = ParsedMessage(
                content=content,
                parsed=parsed_obj,
                refusal=refusal,
                role=message.get("role", "assistant"),
                tool_calls=message.get("tool_calls")
            )
            
            parsed_choice = ParsedChoice(
                message=parsed_message,
                index=i,
                finish_reason=choice.get("finish_reason"),
                logprobs=choice.get("logprobs")
            )
            
            parsed_choices.append(parsed_choice)
        
        return ParsedChatCompletion(
            id=response_data.get("id", ""),
            choices=parsed_choices,
            created=response_data.get("created", 0),
            model=response_data.get("model", ""),
            object=response_data.get("object", "chat.completion"),
            system_fingerprint=response_data.get("system_fingerprint"),
            usage=response_data.get("usage")
        )


def create_anthropic_tools_from_models(*models: Type[Union[BaseModel, 'SatyaModel']]) -> List[Dict[str, Any]]:
    """
    Create Anthropic-compatible tool definitions from Pydantic or Satya models.
    
    Args:
        *models: Pydantic BaseModel or Satya Model classes to convert to tools
        
    Returns:
        List of tool definitions compatible with Anthropic's Messages API
    """
    return [pydantic_tool_schema(model) for model in models]


def create_openai_tools_from_models(*models: Type[Union[BaseModel, 'SatyaModel']]) -> List[Dict[str, Any]]:
    """
    Create OpenAI-compatible function tool definitions from Pydantic or Satya models.
    
    Args:
        *models: Pydantic BaseModel or Satya Model classes to convert to tools
        
    Returns:
        List of function tool definitions compatible with OpenAI's Chat Completions API
    """
    return [pydantic_function_tool(model) for model in models]


def parse_tool_call_arguments(tool_call: Dict[str, Any], model: Type[Union[BaseModel, 'SatyaModel']]) -> Union[BaseModel, 'SatyaModel']:
    """
    Parse and validate tool call arguments against a Pydantic or Satya model.
    
    Args:
        tool_call: Tool call data from API response
        model: Pydantic BaseModel or Satya Model to validate against
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If arguments don't match model schema
    """
    function = tool_call.get("function", {})
    arguments = function.get("arguments", {})
    
    # Handle case where arguments is a JSON string
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in tool call arguments: {e}")
    
    return _validate_with_model(model, arguments)


# Helper functions for backward compatibility
def to_response_format(model: Type[Union[BaseModel, 'SatyaModel']], name: Optional[str] = None) -> Dict[str, Any]:
    """Convert Pydantic or Satya model to response_format dict (OpenAI style)"""
    return ResponseFormat.from_model(model, name=name)


def to_tool_schema(model: Type[Union[BaseModel, 'SatyaModel']]) -> Dict[str, Any]:
    """Convert Pydantic or Satya model to tool schema dict"""
    return pydantic_function_tool(model)


# Test harness - runs when file is executed directly
if __name__ == "__main__":
    import json
    import asyncio
    import os
    from dotenv import load_dotenv
    
    print("🧪 Bhumi Structured Outputs Test Suite")
    print("=" * 50)
    
    # Test 1: Pydantic Model
    print("\n1️⃣ Testing Pydantic Model...")
    from pydantic import BaseModel, Field as PydanticField
    
    class PydanticUser(BaseModel):
        name: str = PydanticField(description="User name")
        age: int = PydanticField(description="User age")
    
    try:
        schema = _get_model_schema(PydanticUser)
        print("✅ Pydantic schema generation works")
        
        response_format = ResponseFormat.from_model(PydanticUser)
        print("✅ Pydantic response format works")
        
        validated = _validate_with_model(PydanticUser, {"name": "John", "age": 30})
        print(f"✅ Pydantic validation works: {validated.name}, {validated.age}")
        
    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
    
    # Test 2: Satya Model (if available)
    print("\n2️⃣ Testing Satya Model...")
    if SATYA_AVAILABLE:
        class SatyaUser(SatyaModel):
            name: str = SatyaField(description="User name")
            age: int = SatyaField(description="User age")
        
        try:
            schema = _get_model_schema(SatyaUser)
            print("✅ Satya schema generation works")
            print(f"   Schema type: {schema.get('type')}")
            print(f"   Properties: {list(schema.get('properties', {}).keys())}")
            
            response_format = ResponseFormat.from_model(SatyaUser)
            print("✅ Satya response format works")
            
            validated = _validate_with_model(SatyaUser, {"name": "Alice", "age": 25})
            print(f"✅ Satya validation works: {validated.name}, {validated.age}")
            
        except Exception as e:
            print(f"❌ Satya test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ Satya not available - install with: pip install satya")
    
    # Test 3: Parser Test
    print("\n3️⃣ Testing Response Parser...")
    try:
        parser = StructuredOutputParser(PydanticUser)
        
        mock_response = {
            'id': 'test-123',
            'object': 'chat.completion',
            'created': 1234567890,
            'model': 'gpt-4',
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': '{"name": "Bob", "age": 35}'
                },
                'finish_reason': 'stop'
            }]
        }
        
        parsed = parser.parse_response(mock_response)
        if parsed.choices[0].message.parsed:
            user = parsed.choices[0].message.parsed
            print(f"✅ Parser works: {user.name}, {user.age}")
        else:
            print("❌ Parser failed to parse mock response")
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
    
    # Test 4: Live API Test (if API key available)
    print("\n4️⃣ Testing Live API (with timeout)...")
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        from bhumi.base_client import BaseLLMClient, LLMConfig
        
        async def test_live_api():
            try:
                config = LLMConfig(api_key=api_key, model="openai/gpt-4o-mini")
                client = BaseLLMClient(config)
                
                completion = await client.parse(
                    messages=[{"role": "user", "content": "Create user named Test, age 99"}],
                    response_format=PydanticUser,
                    timeout=15.0  # 15 second timeout
                )
                
                if completion.parsed:
                    print(f"✅ Live API works: {completion.parsed.name}, {completion.parsed.age}")
                else:
                    print("❌ Live API returned no parsed data")
                    
            except Exception as e:
                print(f"❌ Live API test failed: {e}")
        
        asyncio.run(test_live_api())
    else:
        print("⚠️ No OPENAI_API_KEY found - skipping live API test")
    
    print("\n" + "=" * 50)
    print("🎉 Test Suite Complete!")
    print("\n💡 Usage:")
    print("   from bhumi.structured_outputs import ResponseFormat, StructuredOutputParser")
    print("   from bhumi import BaseLLMClient")
    print("   completion = await client.parse(messages=..., response_format=YourModel)")
    print("   data = completion.parsed  # Your validated model instance")
