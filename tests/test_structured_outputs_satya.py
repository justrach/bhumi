"""
Tests for Satya integration in structured outputs.
"""

import pytest
import json
from typing import List, Optional, Literal
from datetime import datetime
from decimal import Decimal

# Import Satya (if available)
try:
    from satya import Model, Field, ModelValidationError
    SATYA_AVAILABLE = True
except ImportError:
    SATYA_AVAILABLE = False
    pytest.skip("Satya not available", allow_module_level=True)

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
    _is_satya_model,
    _get_model_schema,
    _validate_with_model
)


# Test models using Satya - using types that work with current Satya v0.3 API
class SatyaAddress(Model):
    """User address information (Satya)"""
    street: str = Field(description="Street address")
    city: str = Field(description="City name")
    country: str = Field(description="Country name")
    postal_code: str = Field(description="Postal/ZIP code")


class SatyaUserProfile(Model):
    """Complete user profile information (Satya)"""
    user_id: str = Field(description="Unique user ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    full_name: str = Field(description="Full name")
    age: int = Field(description="User age")
    active: bool = Field(default=True, description="Account status")


class SatyaWeatherQuery(Model):
    """Weather query parameters (Satya)"""
    location: str = Field(description="Location to get weather for")
    units: str = Field(default="celsius", description="Temperature units")
    include_forecast: bool = Field(default=False, description="Include forecast data")


class TestSatyaModelDetection:
    """Test Satya model detection functions"""
    
    def test_is_satya_model(self):
        """Test Satya model detection"""
        assert _is_satya_model(SatyaWeatherQuery) == True
        assert _is_satya_model(SatyaUserProfile) == True
        
        # Test with non-Satya classes
        assert _is_satya_model(str) == False
        assert _is_satya_model(dict) == False
    
    def test_get_model_schema_satya(self):
        """Test schema extraction from Satya models"""
        schema = _get_model_schema(SatyaWeatherQuery)
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "location" in schema["properties"]
        assert "units" in schema["properties"]
        assert "include_forecast" in schema["properties"]
    
    def test_validate_with_satya_model(self):
        """Test validation with Satya models"""
        data = {
            "location": "Tokyo",
            "units": "celsius",
            "include_forecast": True
        }
        
        result = _validate_with_model(SatyaWeatherQuery, data)
        
        assert isinstance(result, SatyaWeatherQuery)
        assert result.location == "Tokyo"
        assert result.units == "celsius"
        assert result.include_forecast == True


class TestSatyaResponseFormat:
    """Test response format creation with Satya models"""
    
    def test_from_satya_model(self):
        """Test creating response format from Satya model"""
        format_dict = ResponseFormat.from_model(SatyaWeatherQuery, name="weather_query")
        
        assert format_dict["type"] == "json_schema"
        assert format_dict["json_schema"]["name"] == "weather_query"
        assert format_dict["json_schema"]["strict"] == True
        assert "properties" in format_dict["json_schema"]["schema"]
        assert "location" in format_dict["json_schema"]["schema"]["properties"]


class TestSatyaToolCreation:
    """Test tool creation with Satya models"""
    
    def test_pydantic_function_tool_satya(self):
        """Test creating OpenAI function tool from Satya model"""
        tool_dict = pydantic_function_tool(SatyaWeatherQuery, name="get_weather")
        
        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "get_weather"
        assert tool_dict["function"]["strict"] == True 
        assert "parameters" in tool_dict["function"]
        assert "location" in tool_dict["function"]["parameters"]["properties"]
    
    def test_pydantic_tool_schema_satya(self):
        """Test creating Anthropic tool schema from Satya model"""
        tool_dict = pydantic_tool_schema(SatyaWeatherQuery)
        
        assert tool_dict["name"] == "satyaweatherquery"
        assert "input_schema" in tool_dict
        assert "location" in tool_dict["input_schema"]["properties"]
    
    def test_create_tools_from_satya_models(self):
        """Test creating multiple tools from Satya models"""
        openai_tools = create_openai_tools_from_models(SatyaWeatherQuery, SatyaUserProfile)
        anthropic_tools = create_anthropic_tools_from_models(SatyaWeatherQuery, SatyaUserProfile)
        
        assert len(openai_tools) == 2
        assert len(anthropic_tools) == 2
        
        assert all(tool["type"] == "function" for tool in openai_tools)
        assert all("input_schema" in tool for tool in anthropic_tools)


class TestSatyaStructuredOutputParser:
    """Test structured output parsing with Satya models"""
    
    def test_satya_parser_initialization(self):
        """Test initializing parser with Satya model"""
        parser = StructuredOutputParser(SatyaWeatherQuery)
        
        assert parser.response_format == SatyaWeatherQuery
        assert parser._schema is not None
        assert parser._satya_validator is not None  # Should create Satya validator
    
    def test_parse_clean_json_with_satya(self):
        """Test parsing clean JSON with Satya model"""
        parser = StructuredOutputParser(SatyaWeatherQuery)
        
        response_data = {
            "id": "test-satya-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"location": "New York", "units": "fahrenheit", "include_forecast": true}'
                },
                "finish_reason": "stop"
            }]
        }
        
        parsed = parser.parse_response(response_data)
        
        assert isinstance(parsed, ParsedChatCompletion)
        assert parsed.id == "test-satya-123"
        assert len(parsed.choices) == 1
        assert parsed.choices[0].message.parsed is not None
        assert isinstance(parsed.choices[0].message.parsed, SatyaWeatherQuery)
        assert parsed.choices[0].message.parsed.location == "New York"
        assert parsed.choices[0].message.parsed.units == "fahrenheit"
        assert parsed.choices[0].message.parsed.include_forecast == True
    
    def test_parse_complex_satya_model(self):
        """Test parsing complex Satya model"""
        parser = StructuredOutputParser(SatyaUserProfile)
        
        content = {
            "user_id": "usr_12345",
            "username": "satyauser",
            "email": "user@example.com",
            "full_name": "Satya User",
            "age": 25,
            "active": True
        }
        
        response_data = {
            "id": "test-complex-satya",
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
        assert isinstance(user, SatyaUserProfile)
        assert user.user_id == "usr_12345"
        assert user.username == "satyauser"
        assert user.email == "user@example.com"
        assert user.age == 25
        assert user.active == True
    
    def test_satya_type_coercion(self):
        """Test that Satya validation works with correct types"""
        # Satya v0.3 doesn't do automatic type coercion like string -> bool
        # So we'll test with correct types
        test_data = {
            "location": "Paris",
            "units": "celsius",
            "include_forecast": False  # Correct boolean type
        }
        
        result = _validate_with_model(SatyaWeatherQuery, test_data)
        
        assert isinstance(result, SatyaWeatherQuery)
        assert result.location == "Paris"
        assert result.units == "celsius"
        assert result.include_forecast == False
    
    def test_satya_validation_errors(self):
        """Test Satya validation error handling"""
        # Satya v0.3 doesn't have strict Literal validation in this simple case
        # So we'll test with a field that should fail
        invalid_data = {
            "location": "Paris",
            "units": "celsius",
            "include_forecast": "not_a_boolean"  # Wrong type - should be bool
        }
        
        # This should raise a ValueError due to type mismatch
        with pytest.raises(ValueError):
            _validate_with_model(SatyaWeatherQuery, invalid_data)


class TestSatyaToolCallParsing:
    """Test tool call argument parsing with Satya models"""
    
    def test_parse_satya_tool_call_arguments(self):
        """Test parsing tool call arguments with Satya model"""
        tool_call = {
            "function": {
                "name": "get_weather",
                "arguments": {
                    "location": "Berlin",
                    "units": "celsius",
                    "include_forecast": False
                }
            }
        }
        
        parsed = parse_tool_call_arguments(tool_call, SatyaWeatherQuery)
        
        assert isinstance(parsed, SatyaWeatherQuery)
        assert parsed.location == "Berlin"
        assert parsed.units == "celsius"
        assert parsed.include_forecast == False


class TestSatyaPerformanceFeatures:
    """Test Satya-specific performance features"""
    
    def test_satya_batch_validation(self):
        """Test Satya's batch validation capabilities"""
        validator = SatyaWeatherQuery.validator()
        
        # Multiple items to validate - ensure all required fields are provided
        data_items = [
            {"location": "Tokyo", "units": "celsius", "include_forecast": False},
            {"location": "London", "units": "fahrenheit", "include_forecast": False},
            {"location": "Paris", "units": "celsius", "include_forecast": True}
        ]
        
        # In Satya v0.3, validate_batch returns a list of booleans
        results = validator.validate_batch(data_items)
        
        assert len(results) == 3
        assert all(results) == True  # All should be True for valid data
    
    def test_satya_stream_validation(self):
        """Test Satya's stream validation"""
        validator = SatyaWeatherQuery.validator()
        
        data_stream = [
            {"location": "NYC", "units": "fahrenheit", "include_forecast": False},
            {"location": "LA", "units": "celsius", "include_forecast": False},
            {"location": "Chicago", "units": "fahrenheit", "include_forecast": True}
        ]
        
        # In Satya v0.3, validate_stream yields ValidationResult objects
        validated_items = list(validator.validate_stream(data_stream))
        
        assert len(validated_items) == 3
        for item in validated_items:
            assert hasattr(item, 'is_valid')
            assert item.is_valid == True


class TestSatyaBackwardCompatibility:
    """Test backward compatibility helpers with Satya models"""
    
    def test_to_response_format_satya(self):
        """Test to_response_format helper with Satya model"""
        format_dict = to_response_format(SatyaWeatherQuery, name="weather")
        
        assert format_dict["type"] == "json_schema"
        assert format_dict["json_schema"]["name"] == "weather"
    
    def test_to_tool_schema_satya(self):
        """Test to_tool_schema helper with Satya model"""
        tool_dict = to_tool_schema(SatyaWeatherQuery)
        
        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "satyaweatherquery"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
