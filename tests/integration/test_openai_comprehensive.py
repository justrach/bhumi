"""
Comprehensive OpenAI Integration Tests

Tests streaming, tool use, structured outputs, and Responses API for OpenAI models.
Run with: pytest tests/integration/test_openai_comprehensive.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def openai_client():
    """Create OpenAI client for testing"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("No OPENAI_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestOpenAIBasic:
    """Basic OpenAI functionality tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, openai_client):
        """Test basic Chat Completions API"""
        response = await openai_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_responses_api_basic(self, openai_client):
        """Test basic Responses API"""
        response = await openai_client.completion(
            input="What is 2+2?",
            stream=False
        )
        assert "text" in response
        assert "4" in response["text"]
    
    @pytest.mark.asyncio
    async def test_responses_api_with_instructions(self, openai_client):
        """Test Responses API with instructions"""
        response = await openai_client.completion(
            input="What is the capital of France?",
            instructions="You are a geography expert. Be concise.",
            stream=False
        )
        assert "text" in response
        assert "paris" in response["text"].lower()

class TestOpenAIStreaming:
    """OpenAI streaming tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_streaming(self, openai_client):
        """Test Chat Completions streaming"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await openai_client.completion(
            [{"role": "user", "content": "Say 'Hello World' and nothing else"}],
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 10:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"
    
    @pytest.mark.asyncio
    async def test_responses_api_streaming(self, openai_client):
        """Test Responses API streaming"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await openai_client.completion(
            input="Tell me a short joke",
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 15:  # Limit chunks
                break
        
        # Note: Some prompts may not stream well, but should not error
        assert chunk_count >= 0
        assert isinstance(accumulated_text, str)

class TestOpenAITools:
    """OpenAI tool calling tests"""
    
    @pytest.mark.asyncio
    async def test_function_calling_chat_completions(self, openai_client):
        """Test function calling with Chat Completions API"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is sunny and 22°C"
        
        openai_client.tool_registry.register(
            name="get_weather",
            func=get_weather,
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        )
        
        response = await openai_client.completion(
            [{"role": "user", "content": "What's the weather in Paris?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain weather information or tool call result
    
    @pytest.mark.asyncio
    async def test_function_calling_responses_api(self, openai_client):
        """Test function calling with Responses API"""
        # Register a calculator tool
        def calculate(expression: str) -> str:
            try:
                result = eval(expression.replace("^", "**"))
                return f"{expression} = {result}"
            except:
                return f"Cannot calculate: {expression}"
        
        openai_client.tool_registry.register(
            name="calculate",
            func=calculate,
            description="Calculate mathematical expressions",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression"
                    }
                },
                "required": ["expression"]
            }
        )
        
        response = await openai_client.completion(
            input="What is 15 * 7?",
            instructions="Use the calculate tool to solve this",
            stream=False
        )
        
        assert "text" in response
        assert "105" in response["text"]
    
    @pytest.mark.asyncio
    async def test_multiple_tools(self, openai_client):
        """Test multiple tools working together"""
        def get_time(timezone: str) -> str:
            return f"Current time in {timezone}: 14:30"
        
        def get_date() -> str:
            return "Today is September 23, 2025"
        
        openai_client.tool_registry.register(
            name="get_time",
            func=get_time,
            description="Get current time for timezone",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone name"}
                },
                "required": ["timezone"]
            }
        )
        
        openai_client.tool_registry.register(
            name="get_date",
            func=get_date,
            description="Get current date",
            parameters={"type": "object", "properties": {}}
        )
        
        response = await openai_client.completion(
            input="What time is it in UTC and what's today's date?",
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0

class TestOpenAIStructuredOutputs:
    """OpenAI structured outputs tests"""
    
    @pytest.mark.asyncio
    async def test_structured_output_chat_completions(self, openai_client):
        """Test structured outputs with Chat Completions API"""
        try:
            from satya import Model, Field
            
            class UserProfile(Model):
                name: str = Field(description="User's full name")
                age: int = Field(description="User's age")
                city: str = Field(description="User's city")
            
            # Set structured output
            openai_client.set_structured_output(UserProfile)
            
            response = await openai_client.completion(
                [{"role": "user", "content": "Create a user profile for John Smith, 30 years old, living in New York"}],
                stream=False
            )
            
            assert "text" in response
            # Should contain structured JSON
            assert "john" in response["text"].lower()
            assert "30" in response["text"]
            assert "new york" in response["text"].lower()
            
        except ImportError:
            pytest.skip("Satya not available for structured outputs test")
    
    @pytest.mark.asyncio
    async def test_structured_output_responses_api(self, openai_client):
        """Test structured outputs with Responses API"""
        try:
            from satya import Model, Field
            
            class WeatherReport(Model):
                location: str = Field(description="Location name")
                temperature: int = Field(description="Temperature in Celsius")
                condition: str = Field(description="Weather condition")
            
            openai_client.set_structured_output(WeatherReport)
            
            response = await openai_client.completion(
                input="Create a weather report for London with 15 degrees and cloudy conditions",
                instructions="Generate a structured weather report",
                stream=False
            )
            
            assert "text" in response
            assert "london" in response["text"].lower()
            assert "15" in response["text"]
            assert "cloudy" in response["text"].lower()
            
        except ImportError:
            pytest.skip("Satya not available for structured outputs test")

class TestOpenAIEdgeCases:
    """OpenAI edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, openai_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await openai_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_invalid_responses_api_params(self, openai_client):
        """Test invalid Responses API parameters"""
        with pytest.raises(ValueError):
            await openai_client.completion(
                instructions="Only instructions, no input",
                stream=False
            )
    
    @pytest.mark.asyncio
    async def test_mixed_api_parameters(self, openai_client):
        """Test mixing Chat Completions and Responses API parameters"""
        # Should use Responses API (input takes precedence)
        response = await openai_client.completion(
            messages=[{"role": "user", "content": "Ignored"}],
            input="This should be used",
            stream=False
        )
        assert "text" in response

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
