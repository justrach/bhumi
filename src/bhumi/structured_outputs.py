"""
Structured outputs implementation using Satya for high-performance validation.

This module provides:
- JSON schema generation from Satya models
- Response format configuration for structured outputs
- Parsed completion types with automatic validation
- Tool definition helpers for structured tool calls
- High-performance validation with Satya v0.3.7
"""

from __future__ import annotations

import json
import inspect
from typing import Type, TypeVar, Dict, Any, Optional, List
from dataclasses import dataclass

# Import Satya (required for structured outputs)
try:
    from satya import Model as SatyaModel, Field as SatyaField, ValidationError as SatyaValidationError
    SATYA_AVAILABLE = True
except ImportError:
    raise ImportError(
        "Satya is required for structured outputs. Install with: pip install 'satya>=0.3.7'"
    )

# Type variables for Satya models
T = TypeVar('T', bound=SatyaModel)
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


class ContentFilterError(StructuredOutputError):
    """Raised when completion is filtered by content policy"""
    pass


# Alias for backward compatibility
ContentFilterFinishReasonError = ContentFilterError


def _is_satya_model(model_class: Type) -> bool:
    """Check if a class is a Satya model"""
    return (
        SATYA_AVAILABLE and
        inspect.isclass(model_class) and 
        issubclass(model_class, SatyaModel)
    )


def _get_model_schema(model_class: Type[SatyaModel]) -> Dict[str, Any]:
    """Get JSON schema from Satya model"""
    if not _is_satya_model(model_class):
        raise ValueError(f"Unsupported model type: {model_class}. Must be Satya Model.")
    
    # Use Satya v0.3.7's built-in OpenAI-compatible schema generation
    try:
        return model_class.openai_schema()
    except AttributeError:
        # Fallback for older Satya versions
        return model_class.json_schema()


def _validate_with_model(model_class: Type[SatyaModel], data: Dict[str, Any]) -> SatyaModel:
    """Validate data with Satya model"""
    if not _is_satya_model(model_class):
        raise ValueError(f"Unsupported model type: {model_class}. Must be Satya Model.")
    
    try:
        # Use the Pydantic-compatible method first
        if hasattr(model_class, 'model_validate'):
            return model_class.model_validate(data)
        else:
            # Fallback to direct instantiation
            return model_class(**data)
    except (SatyaValidationError, ValueError, TypeError) as e:
        if isinstance(e, SatyaValidationError):
            raise SchemaValidationError(f"Satya validation failed: {e}")
        else:
            raise ValueError(f"Satya model validation failed for {model_class.__name__}: {e}")


def satya_function_tool(model: Type[SatyaModel], *, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a Satya model to a function tool definition with strict JSON schema.
    Similar to OpenAI's function tool helper.
    
    Args:
        model: Satya Model class to convert
        name: Optional name for the tool (defaults to model name)
        description: Optional description (defaults to model docstring)
    
    Returns:
        Function tool definition dict compatible with OpenAI's Chat Completions API
    """
    schema = _get_model_schema(model)
    tool_name = name or model.__name__.lower()
    tool_description = description or model.__doc__ or f"Tool using {model.__name__} schema"
    
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": schema,
            "strict": True  # Enable strict mode for better validation
        }
    }


def satya_tool_schema(model: Type[SatyaModel]) -> Dict[str, Any]:
    """
    Convert Satya model to Anthropic-style tool schema.
    
    Args:
        model: Satya Model class to convert
        
    Returns:
        Tool schema dict compatible with Anthropic's tool calling format
    """
    schema = _get_model_schema(model)
    
    return {
        "name": model.__name__.lower(),
        "description": model.__doc__ or f"Tool using {model.__name__} schema",
        "input_schema": schema
    }


@dataclass
class ResponseFormat:
    """
    Response format configuration for structured outputs.
    Compatible with OpenAI's response_format parameter.
    """
    type: str = "json_schema"
    json_schema: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def from_model(model: Type[SatyaModel], *, name: Optional[str] = None, strict: bool = False) -> Dict[str, Any]:
        """Create response format from Satya model"""
        schema = _get_model_schema(model)
        model_name = name or model.__name__.lower()
        
        return {
            "type": "json_schema",
            "json_schema": {
                "name": model_name,
                "schema": schema,
                "strict": strict
            }
        }


class StructuredOutputParser:
    """
    Parser for handling structured outputs with automatic validation.
    Follows patterns similar to OpenAI's client.chat.completions.parse() method.
    Supports Satya models for high-performance validation.
    """
    
    def __init__(self, response_format: Type[SatyaModel]):
        self.response_format = response_format
        self.model_name = response_format.__name__
    
    def parse_response(self, response: Dict[str, Any]) -> 'ParsedCompletion':
        """Parse and validate API response"""
        
        # Handle different response formats
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            
            # Check finish reason
            finish_reason = choice.get('finish_reason')
            if finish_reason == 'length':
                raise LengthFinishReasonError("Completion was truncated due to length limits")
            elif finish_reason == 'content_filter':
                raise ContentFilterError("Completion was filtered by content policy")
            
            # Extract content
            message = choice.get('message', {})
            content = message.get('content', '')
            
            # Handle refusal
            if message.get('refusal'):
                raise SchemaValidationError(f"Model refused to generate structured output: {message['refusal']}")
            
        elif 'content' in response:
            # Direct content response
            content = response['content']
        else:
            raise SchemaValidationError("Invalid response format: no content found")
        
        # Parse JSON content
        try:
            if isinstance(content, str):
                parsed_data = json.loads(content)
            else:
                parsed_data = content
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Invalid JSON in response: {e}")
        
        # Validate against model
        try:
            validated_model = _validate_with_model(self.response_format, parsed_data)
        except (SchemaValidationError, ValueError) as e:
            raise SchemaValidationError(f"Response validation failed: {e}")
        
        return ParsedCompletion(
            id=response.get('id', 'unknown'),
            choices=[
                ParsedChoice(
                    finish_reason=response.get('choices', [{}])[0].get('finish_reason', 'stop'),
                    index=0,
                    message=ParsedMessage(
                        content=content,
                        parsed=validated_model,
                        refusal=None,
                        role='assistant'
                    )
                )
            ],
            created=response.get('created', 0),
            model=response.get('model', 'unknown'),
            object='chat.completion.parsed',
            system_fingerprint=response.get('system_fingerprint'),
            usage=response.get('usage', {}),
            parsed=validated_model  # Direct access to parsed object
        )


@dataclass
class ParsedMessage:
    """Parsed message with validated structured output"""
    content: str
    parsed: Optional[SatyaModel]
    refusal: Optional[str]
    role: str


@dataclass
class ParsedChoice:
    """Parsed choice with structured output"""
    finish_reason: str
    index: int
    message: ParsedMessage


@dataclass
class ParsedCompletion:
    """
    Parsed completion response with structured output validation.
    Similar to OpenAI's ParsedChatCompletion type.
    """
    id: str
    choices: List[ParsedChoice]
    created: int
    model: str
    object: str
    system_fingerprint: Optional[str]
    usage: Dict[str, Any]
    parsed: Optional[SatyaModel]  # Direct access to the parsed object


# Alias for backward compatibility
ParsedChatCompletion = ParsedCompletion


# Tool creation helpers
def create_anthropic_tools_from_models(*models: Type[SatyaModel]) -> List[Dict[str, Any]]:
    """
    Create Anthropic-compatible tool definitions from Satya models.
    
    Args:
        *models: Satya Model classes to convert to tools
        
    Returns:
        List of tool definitions compatible with Anthropic's Messages API
    """
    return [satya_tool_schema(model) for model in models]


def create_openai_tools_from_models(*models: Type[SatyaModel]) -> List[Dict[str, Any]]:
    """
    Create OpenAI-compatible function tool definitions from Satya models.
    
    Args:
        *models: Satya Model classes to convert to tools
        
    Returns:
        List of function tool definitions compatible with OpenAI's Chat Completions API
    """
    return [satya_function_tool(model) for model in models]


def parse_tool_call_arguments(tool_call: Dict[str, Any], model: Type[SatyaModel]) -> SatyaModel:
    """
    Parse and validate tool call arguments against a Satya model.
    
    Args:
        tool_call: Tool call data from API response
        model: Satya Model to validate against
        
    Returns:
        Validated model instance
    """
    # Extract arguments from tool call
    if 'function' in tool_call and 'arguments' in tool_call['function']:
        args_str = tool_call['function']['arguments']
        if isinstance(args_str, str):
            args_data = json.loads(args_str)
        else:
            args_data = args_str
    elif 'arguments' in tool_call:
        args_data = tool_call['arguments']
    else:
        raise ValueError("Invalid tool call format: no arguments found")
    
    return _validate_with_model(model, args_data)


# Helper functions for backward compatibility
def to_response_format(model: Type[SatyaModel], name: Optional[str] = None) -> Dict[str, Any]:
    """Convert Satya model to response_format dict (OpenAI style)"""
    return ResponseFormat.from_model(model, name=name)


def to_tool_schema(model: Type[SatyaModel]) -> Dict[str, Any]:
    """Convert Satya model to tool schema dict"""
    return satya_function_tool(model)


# Test harness - runs when file is executed directly
if __name__ == "__main__":
    import asyncio
    import os
    
    print("🧪 Bhumi Structured Outputs Test Suite (Satya Only)")
    print("=" * 60)
    
    # Test 1: Satya Model
    print("\n1️⃣ Testing Satya Model...")
    if SATYA_AVAILABLE:
        try:
            class SatyaUser(SatyaModel):
                name: str = SatyaField(description="User name")
                age: int = SatyaField(description="User age")
            
            schema = _get_model_schema(SatyaUser)
            print("✅ Satya schema generation works")
            
            response_format = ResponseFormat.from_model(SatyaUser)
            print("✅ Satya response format works")
            
            validated = _validate_with_model(SatyaUser, {"name": "Jane", "age": 25})
            print(f"✅ Satya validation works: {validated.name}, {validated.age}")
            
        except Exception as e:
            print(f"❌ Satya test failed: {e}")
    else:
        print("❌ Satya not available - install with: pip install 'satya>=0.3.7'")
    
    # Test 2: Parser Test
    print("\n2️⃣ Testing Response Parser...")
    if SATYA_AVAILABLE:
        try:
            parser = StructuredOutputParser(SatyaUser)
            
            mock_response = {
                'id': 'test-123',
                'choices': [{
                    'message': {
                        'content': '{"name": "Parser Test", "age": 42}',
                        'role': 'assistant'
                    },
                    'finish_reason': 'stop'
                }],
                'created': 1234567890,
                'model': 'test-model'
            }
            
            parsed = parser.parse_response(mock_response)
            print(f"✅ Parser works: {parsed.parsed.name}, {parsed.parsed.age}")
            
        except Exception as e:
            print(f"❌ Parser test failed: {e}")
    
    # Test 3: Tool Schema Generation
    print("\n3️⃣ Testing Tool Schema Generation...")
    if SATYA_AVAILABLE:
        try:
            tool_schema = satya_function_tool(SatyaUser)
            print("✅ OpenAI tool schema generation works")
            
            anthropic_schema = satya_tool_schema(SatyaUser)
            print("✅ Anthropic tool schema generation works")
            
        except Exception as e:
            print(f"❌ Tool schema test failed: {e}")
    
    print(f"\n🎯 Test Summary: Satya v0.3.7 High-Performance Validation")
    print(f"   • 2-7x faster than alternatives")
    print(f"   • OpenAI-compatible schema generation")
    print(f"   • Nested model support")
    print(f"   • Production-ready validation")


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
