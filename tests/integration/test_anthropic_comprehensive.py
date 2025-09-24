"""
Comprehensive Anthropic Integration Tests

Tests streaming, tool use, and structured outputs for Anthropic Claude models.
Run with: pytest tests/integration/test_anthropic_comprehensive.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def anthropic_client():
    """Create Anthropic client for testing"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("No ANTHROPIC_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="anthropic/claude-3-5-sonnet-20241022",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestAnthropicBasic:
    """Basic Anthropic functionality tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, anthropic_client):
        """Test basic Chat Completions API with Anthropic"""
        response = await anthropic_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_system_message(self, anthropic_client):
        """Test system message handling"""
        response = await anthropic_client.completion(
            [
                {"role": "system", "content": "You are a helpful math tutor"},
                {"role": "user", "content": "What is 5 + 3?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "8" in response["text"]
    
    @pytest.mark.asyncio
    async def test_longer_conversation(self, anthropic_client):
        """Test multi-turn conversation"""
        response = await anthropic_client.completion(
            [
                {"role": "user", "content": "My name is Alice"},
                {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                {"role": "user", "content": "What's my name?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "alice" in response["text"].lower()

class TestAnthropicStreaming:
    """Anthropic streaming tests"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, anthropic_client):
        """Test basic streaming with Anthropic"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await anthropic_client.completion(
            [{"role": "user", "content": "Tell me a short joke"}],
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 20:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"
    
    @pytest.mark.asyncio
    async def test_streaming_with_system_message(self, anthropic_client):
        """Test streaming with system message"""
        chunk_count = 0
        
        async for chunk in await anthropic_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Count to 3"}
            ],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 10:
                break
        
        assert chunk_count > 0

class TestAnthropicTools:
    """Anthropic tool calling tests"""
    
    @pytest.mark.asyncio
    async def test_function_calling(self, anthropic_client):
        """Test function calling with Anthropic"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is partly cloudy and 20°C"
        
        anthropic_client.tool_registry.register(
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
        
        response = await anthropic_client.completion(
            [{"role": "user", "content": "What's the weather in London?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain weather information
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self, anthropic_client):
        """Test calculator tool with Anthropic"""
        def calculate(expression: str) -> str:
            try:
                result = eval(expression.replace("^", "**"))
                return f"{expression} = {result}"
            except:
                return f"Cannot calculate: {expression}"
        
        anthropic_client.tool_registry.register(
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
        
        response = await anthropic_client.completion(
            [{"role": "user", "content": "What is 12 * 8?"}],
            stream=False
        )
        
        assert "text" in response
        # Should contain calculation result
    
    @pytest.mark.asyncio
    async def test_multiple_tools_anthropic(self, anthropic_client):
        """Test multiple tools with Anthropic"""
        def get_time(timezone: str) -> str:
            return f"Current time in {timezone}: 15:45"
        
        def get_temperature(city: str) -> str:
            return f"Temperature in {city}: 18°C"
        
        anthropic_client.tool_registry.register(
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
        
        anthropic_client.tool_registry.register(
            name="get_temperature",
            func=get_temperature,
            description="Get temperature for city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        )
        
        response = await anthropic_client.completion(
            [{"role": "user", "content": "What time is it in EST and what's the temperature in Boston?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0

class TestAnthropicStructuredOutputs:
    """Anthropic structured outputs tests"""
    
    @pytest.mark.asyncio
    async def test_json_output_prompt_engineering(self, anthropic_client):
        """Test JSON output using prompt engineering (Anthropic approach)"""
        response = await anthropic_client.completion(
            [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that always responds with valid JSON. Generate a user profile with name, age, and city fields."
                },
                {
                    "role": "user", 
                    "content": "Create a profile for Sarah Johnson, 28 years old, living in Seattle. Respond only with JSON."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Try to parse as JSON
        try:
            # Extract JSON from response (might have extra text)
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                assert "name" in json_data or "Name" in json_data
                assert "age" in json_data or "Age" in json_data
                assert "city" in json_data or "City" in json_data
            else:
                # If no JSON found, at least check content
                assert "sarah" in response_text.lower()
                assert "28" in response_text
                assert "seattle" in response_text.lower()
        except json.JSONDecodeError:
            # If JSON parsing fails, check for expected content
            assert "sarah" in response_text.lower()
            assert "28" in response_text
            assert "seattle" in response_text.lower()
    
    @pytest.mark.asyncio
    async def test_structured_output_with_satya(self, anthropic_client):
        """Test structured outputs with Satya (if available)"""
        try:
            from satya import Model, Field
            
            class BookReview(Model):
                title: str = Field(description="Book title")
                author: str = Field(description="Book author")
                rating: int = Field(description="Rating from 1-5")
                summary: str = Field(description="Brief summary")
            
            anthropic_client.set_structured_output(BookReview)
            
            response = await anthropic_client.completion(
                [{"role": "user", "content": "Create a book review for '1984' by George Orwell, rating 5/5"}],
                stream=False
            )
            
            assert "text" in response
            assert "1984" in response["text"]
            assert "orwell" in response["text"].lower()
            assert "5" in response["text"]
            
        except ImportError:
            pytest.skip("Satya not available for structured outputs test")

class TestAnthropicEdgeCases:
    """Anthropic edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, anthropic_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await anthropic_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, anthropic_client):
        """Test with very long message"""
        long_message = "Tell me about AI. " * 100  # Repeat to make it long
        
        response = await anthropic_client.completion(
            [{"role": "user", "content": long_message}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_special_characters(self, anthropic_client):
        """Test with special characters"""
        response = await anthropic_client.completion(
            [{"role": "user", "content": "Translate: Hello! How are you? 你好！"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
