"""
Tests for the new structured outputs implementation following OpenAI/Anthropic patterns.
"""

import pytest
import json
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

from bhumi.structured_outputs import (
    StructuredOutputParser,
    ResponseFormat,
    ParsedChatCompletion,
    ParsedMessage,
    ParsedChoice,
    pydantic_function_tool,
    pydantic_tool_schema,
    create_anthropic_tools_from_models,
    create_openai_tools_from_models,
    parse_tool_call_arguments,
    to_response_format,
    to_tool_schema,
    StructuredOutputError,
    SchemaValidationError,
    LengthFinishReasonError,
    ContentFilterFinishReasonError
)


# Test models
class Address(BaseModel):
    """User address information"""
    street: str = Field(description="Street address")
    city: str = Field(description="City name")
    state: str = Field(description="State or province")
    country: str = Field(description="Country name")
    postal_code: str = Field(description="Postal/ZIP code")


class UserProfile(BaseModel):
    """Complete user profile information"""
    user_id: str = Field(pattern="^usr_[a-zA-Z0-9]+$", description="Unique user ID")
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: str = Field(description="Email address")
    full_name: str = Field(min_length=1, description="Full name")
    age: int = Field(ge=13, le=120, description="User age")
    address: Address = Field(description="User's address")
    created_at: datetime = Field(description="Account creation timestamp")


class WeatherQuery(BaseModel):
    """Weather query parameters"""
    location: str = Field(description="Location to get weather for")
    units: Literal["celsius", "fahrenheit"] = Field(default="celsius", description="Temperature units")
    include_forecast: bool = Field(default=False, description="Include forecast data")


class TestResponseFormat:
    """Test response format creation"""
    
    def test_json_object_format(self):
        """Test creating JSON object response format"""
        format_dict = ResponseFormat.json_object()
        assert format_dict == {"type": "json_object"}
    
    def test_json_schema_format(self):
        """Test creating JSON schema response format"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        format_dict = ResponseFormat.json_schema(
            schema=schema,
            name="test_schema",
            description="Test schema",
            strict=True
        )
        
        expected = {
            "type": "json_schema", 
            "json_schema": {
                "name": "test_schema",
                "description": "Test schema",
                "schema": schema,
                "strict": True
            }
        }
        assert format_dict == expected
    
    def test_from_model(self):
        """Test creating response format from Pydantic model"""
        format_dict = ResponseFormat.from_model(WeatherQuery, name="weather_query")
        
        assert format_dict["type"] == "json_schema"
        assert format_dict["json_schema"]["name"] == "weather_query"
        assert format_dict["json_schema"]["strict"] == True
        assert "properties" in format_dict["json_schema"]["schema"]
        assert "location" in format_dict["json_schema"]["schema"]["properties"]


class TestPydanticFunctionTool:
    """Test Pydantic function tool conversion"""
    
    def test_basic_conversion(self):
        """Test basic model to function tool conversion"""
        tool_dict = pydantic_function_tool(WeatherQuery)
        
        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "weatherquery"
        assert tool_dict["function"]["strict"] == True
        assert "parameters" in tool_dict["function"]
        assert tool_dict["function"]["parameters"]["type"] == "object"
        assert "location" in tool_dict["function"]["parameters"]["properties"]
    
    def test_custom_name_and_description(self):
        """Test function tool with custom name and description"""
        tool_dict = pydantic_function_tool(
            WeatherQuery,
            name="get_weather",
            description="Get current weather information"
        )
        
        assert tool_dict["function"]["name"] == "get_weather"
        assert tool_dict["function"]["description"] == "Get current weather information"


class TestPydanticToolSchema:
    """Test Anthropic-style tool schema conversion"""
    
    def test_basic_conversion(self):
        """Test basic model to Anthropic tool schema conversion"""
        tool_dict = pydantic_tool_schema(WeatherQuery)
        
        assert tool_dict["name"] == "weatherquery"
        assert "input_schema" in tool_dict
        assert tool_dict["input_schema"]["type"] == "object"
        assert "location" in tool_dict["input_schema"]["properties"]


class TestToolCreation:
    """Test tool creation helpers"""
    
    def test_create_openai_tools_from_models(self):
        """Test creating OpenAI tools from multiple models"""
        tools = create_openai_tools_from_models(WeatherQuery, UserProfile)
        
        assert len(tools) == 2
        assert all(tool["type"] == "function" for tool in tools)
        assert all(tool["function"]["strict"] == True for tool in tools)
    
    def test_create_anthropic_tools_from_models(self):
        """Test creating Anthropic tools from multiple models"""
        tools = create_anthropic_tools_from_models(WeatherQuery, UserProfile)
        
        assert len(tools) == 2
        assert all("input_schema" in tool for tool in tools)
        assert all(tool["input_schema"]["type"] == "object" for tool in tools)


class TestStructuredOutputParser:
    """Test structured output parsing"""
    
    def test_parse_clean_json_response(self):
        """Test parsing clean JSON response"""
        parser = StructuredOutputParser(WeatherQuery)
        
        response_data = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"location": "New York", "units": "celsius", "include_forecast": true}'
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert isinstance(parsed, ParsedChatCompletion)
        assert parsed.id == "test-123"
        assert len(parsed.choices) == 1
        assert parsed.choices[0].message.parsed is not None
        assert parsed.choices[0].message.parsed.location == "New York"
        assert parsed.choices[0].message.parsed.units == "celsius"
        assert parsed.choices[0].message.parsed.include_forecast == True
    
    def test_parse_markdown_json_response(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        parser = StructuredOutputParser(WeatherQuery)
        
        content = '''```json
        {
            "location": "London",
            "units": "fahrenheit",
            "include_forecast": false
        }
        ```'''
        
        response_data = {
            "id": "test-456",
            "object": "chat.completion", 
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert parsed.choices[0].message.parsed is not None
        assert parsed.choices[0].message.parsed.location == "London"
        assert parsed.choices[0].message.parsed.units == "fahrenheit"
    
    def test_parse_mixed_content_response(self):
        """Test parsing JSON embedded in text"""
        parser = StructuredOutputParser(WeatherQuery)
        
        content = '''Here's the weather query you requested:

        {"location": "Tokyo", "units": "celsius", "include_forecast": true}

        This should work perfectly for your needs.'''
        
        response_data = {
            "id": "test-789",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert parsed.choices[0].message.parsed is not None
        assert parsed.choices[0].message.parsed.location == "Tokyo"
    
    def test_parse_invalid_json_response(self):
        """Test handling invalid JSON in response"""
        parser = StructuredOutputParser(WeatherQuery)
        
        response_data = {
            "id": "test-invalid",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is not JSON at all!"
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        # Should not raise exception, but parsed should be None
        assert parsed.choices[0].message.parsed is None
        assert parsed.choices[0].message.content == "This is not JSON at all!"
    
    def test_length_finish_reason_error(self):
        """Test handling length finish reason"""
        parser = StructuredOutputParser(WeatherQuery)
        
        response_data = {
            "id": "test-length",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"location": "incomplete...'
                },
                "finish_reason": "length"
            }]
        }
        
        with pytest.raises(LengthFinishReasonError):
            parser.parse_response(response_data)
    
    def test_content_filter_finish_reason_error(self):
        """Test handling content filter finish reason"""
        parser = StructuredOutputParser(WeatherQuery)
        
        response_data = {
            "id": "test-filter", 
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Filtered content"
                },
                "finish_reason": "content_filter"
            }]
        }
        
        with pytest.raises(ContentFilterFinishReasonError):
            parser.parse_response(response_data)
    
    def test_refusal_handling(self):
        """Test handling model refusal"""
        parser = StructuredOutputParser(WeatherQuery)
        
        response_data = {
            "id": "test-refusal",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "refusal": "I cannot provide this information"
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert parsed.choices[0].message.parsed is None
        assert parsed.choices[0].message.refusal == "I cannot provide this information"


class TestToolCallArgumentParsing:
    """Test parsing tool call arguments"""
    
    def test_parse_valid_arguments(self):
        """Test parsing valid tool call arguments"""
        tool_call = {
            "function": {
                "name": "get_weather",
                "arguments": {
                    "location": "Paris",
                    "units": "celsius",
                    "include_forecast": True
                }
            }
        }
        
        parsed = parse_tool_call_arguments(tool_call, WeatherQuery)
        
        assert isinstance(parsed, WeatherQuery)
        assert parsed.location == "Paris"
        assert parsed.units == "celsius"
        assert parsed.include_forecast == True
    
    def test_parse_json_string_arguments(self):
        """Test parsing arguments provided as JSON string"""
        tool_call = {
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "Berlin", "units": "fahrenheit"}'
            }
        }
        
        parsed = parse_tool_call_arguments(tool_call, WeatherQuery)
        
        assert parsed.location == "Berlin"
        assert parsed.units == "fahrenheit"
    
    def test_parse_invalid_arguments(self):
        """Test handling invalid arguments"""
        tool_call = {
            "function": {
                "name": "get_weather",
                "arguments": {
                    "location": "Madrid",
                    "units": "invalid_unit"  # Not a valid Literal value
                }
            }
        }
        
        with pytest.raises(ValidationError):
            parse_tool_call_arguments(tool_call, WeatherQuery)


class TestBackwardCompatibility:
    """Test backward compatibility helpers"""
    
    def test_to_response_format(self):
        """Test to_response_format helper"""
        format_dict = to_response_format(WeatherQuery, name="weather")
        
        assert format_dict["type"] == "json_schema"
        assert format_dict["json_schema"]["name"] == "weather"
    
    def test_to_tool_schema(self):
        """Test to_tool_schema helper"""
        tool_dict = to_tool_schema(WeatherQuery)
        
        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "weatherquery"


class TestComplexModels:
    """Test with complex nested models"""
    
    def test_nested_model_parsing(self):
        """Test parsing nested models like UserProfile with Address"""
        parser = StructuredOutputParser(UserProfile)
        
        content = {
            "user_id": "usr_12345",
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postal_code": "10001"
            },
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        response_data = {
            "id": "test-nested",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content)
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert parsed.choices[0].message.parsed is not None
        user = parsed.choices[0].message.parsed
        assert user.user_id == "usr_12345"
        assert user.username == "johndoe"
        assert isinstance(user.address, Address)
        assert user.address.city == "New York"
        assert user.address.postal_code == "10001"


# Integration test would require actual API keys, so we'll skip for unit tests
@pytest.mark.skip(reason="Requires API keys for integration testing")
class TestIntegration:
    """Integration tests with real API calls"""
    
    async def test_openai_integration(self):
        """Test with real OpenAI API"""
        # This would test actual API integration
        pass
    
    async def test_anthropic_integration(self):
        """Test with real Anthropic API"""
        # This would test actual API integration
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
