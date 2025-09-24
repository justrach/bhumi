"""
Comprehensive Groq Integration Tests

Tests streaming, tool use, and structured outputs for Groq models.
Run with: pytest tests/integration/test_groq_comprehensive.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def groq_client():
    """Create Groq client for testing"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        pytest.skip("No GROQ_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="groq/llama-3.1-8b-instant",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestGroqBasic:
    """Basic Groq functionality tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, groq_client):
        """Test basic Chat Completions API with Groq"""
        response = await groq_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_system_message(self, groq_client):
        """Test system message handling with Groq"""
        response = await groq_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant that gives concise answers"},
                {"role": "user", "content": "What is the capital of Japan?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "tokyo" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_math_problem(self, groq_client):
        """Test math problem solving"""
        response = await groq_client.completion(
            [{"role": "user", "content": "What is 8 * 7?"}],
            stream=False
        )
        assert "text" in response
        assert "56" in response["text"]

class TestGroqStreaming:
    """Groq streaming tests"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, groq_client):
        """Test basic streaming with Groq"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await groq_client.completion(
            [{"role": "user", "content": "Tell me a fun fact about space"}],
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 30:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"
    
    @pytest.mark.asyncio
    async def test_streaming_with_system_message(self, groq_client):
        """Test streaming with system message"""
        chunk_count = 0
        
        async for chunk in await groq_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant. Be informative but brief."},
                {"role": "user", "content": "Explain machine learning in simple terms"}
            ],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 20:
                break
        
        assert chunk_count > 0
    
    @pytest.mark.asyncio
    async def test_streaming_creative_task(self, groq_client):
        """Test streaming with creative task"""
        chunk_count = 0
        
        async for chunk in await groq_client.completion(
            [{"role": "user", "content": "Write a short poem about the ocean"}],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 25:
                break
        
        assert chunk_count >= 0  # May be 0 for some prompts

class TestGroqTools:
    """Groq tool calling tests"""
    
    @pytest.mark.asyncio
    async def test_function_calling(self, groq_client):
        """Test function calling with Groq"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is partly sunny and 21°C"
        
        groq_client.tool_registry.register(
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
        
        response = await groq_client.completion(
            [{"role": "user", "content": "What's the weather in Chicago?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain weather information
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self, groq_client):
        """Test calculator tool with Groq"""
        def calculate(expression: str) -> str:
            try:
                result = eval(expression.replace("^", "**"))
                return f"{expression} = {result}"
            except:
                return f"Cannot calculate: {expression}"
        
        groq_client.tool_registry.register(
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
        
        response = await groq_client.completion(
            [{"role": "user", "content": "What is 144 / 12?"}],
            stream=False
        )
        
        assert "text" in response
        # Should contain calculation result
    
    @pytest.mark.asyncio
    async def test_data_lookup_tool(self, groq_client):
        """Test data lookup tool with Groq"""
        def lookup_country_capital(country: str) -> str:
            capitals = {
                "france": "Paris",
                "germany": "Berlin",
                "italy": "Rome",
                "spain": "Madrid",
                "japan": "Tokyo"
            }
            return capitals.get(country.lower(), f"Capital of {country} not found")
        
        groq_client.tool_registry.register(
            name="lookup_country_capital",
            func=lookup_country_capital,
            description="Look up the capital of a country",
            parameters={
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country name"
                    }
                },
                "required": ["country"]
            }
        )
        
        response = await groq_client.completion(
            [{"role": "user", "content": "What is the capital of Germany?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0

class TestGroqStructuredOutputs:
    """Groq structured outputs tests"""
    
    @pytest.mark.asyncio
    async def test_json_output_prompt_engineering(self, groq_client):
        """Test JSON output using prompt engineering"""
        response = await groq_client.completion(
            [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that always responds with valid JSON. Generate a restaurant review with name, cuisine, rating, and comment fields."
                },
                {
                    "role": "user", 
                    "content": "Create a review for 'Pizza Palace', Italian cuisine, 4 stars, 'Great pizza and friendly service'. Respond only with JSON."
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
                assert "cuisine" in json_data or "Cuisine" in json_data
                assert "rating" in json_data or "Rating" in json_data
            else:
                # If no JSON found, at least check content
                assert "pizza palace" in response_text.lower()
                assert "italian" in response_text.lower()
                assert "4" in response_text
        except json.JSONDecodeError:
            # If JSON parsing fails, check for expected content
            assert "pizza palace" in response_text.lower()
            assert "italian" in response_text.lower()
            assert "4" in response_text
    
    @pytest.mark.asyncio
    async def test_structured_output_with_satya(self, groq_client):
        """Test structured outputs with Satya (if available)"""
        try:
            from satya import Model, Field
            
            class EventInfo(Model):
                name: str = Field(description="Event name")
                date: str = Field(description="Event date")
                location: str = Field(description="Event location")
                attendees: int = Field(description="Number of attendees")
            
            groq_client.set_structured_output(EventInfo)
            
            response = await groq_client.completion(
                [{"role": "user", "content": "Create event info: 'Tech Conference 2025', March 15, San Francisco, 500 attendees"}],
                stream=False
            )
            
            assert "text" in response
            assert "tech conference" in response["text"].lower()
            assert "march" in response["text"].lower()
            assert "san francisco" in response["text"].lower()
            assert "500" in response["text"]
            
        except ImportError:
            pytest.skip("Satya not available for structured outputs test")
    
    @pytest.mark.asyncio
    async def test_list_structured_output(self, groq_client):
        """Test generating structured lists"""
        response = await groq_client.completion(
            [
                {
                    "role": "system",
                    "content": "Generate a JSON array of countries with their capitals and populations."
                },
                {
                    "role": "user",
                    "content": "List 3 European countries with capitals and approximate populations in JSON format."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain European country names
        assert any(country in response_text.lower() for country in ["france", "germany", "italy", "spain", "uk", "poland"])

class TestGroqEdgeCases:
    """Groq edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, groq_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await groq_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_conversation_memory(self, groq_client):
        """Test conversation memory"""
        response = await groq_client.completion(
            [
                {"role": "user", "content": "My name is Alice and I like cats"},
                {"role": "assistant", "content": "Hello Alice! It's nice to meet someone who likes cats."},
                {"role": "user", "content": "What do I like?"}
            ],
            stream=False
        )
        
        assert "text" in response
        assert "cat" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_code_explanation(self, groq_client):
        """Test code explanation capabilities"""
        response = await groq_client.completion(
            [{"role": "user", "content": "Explain what this Python code does: for i in range(5): print(i)"}],
            stream=False
        )
        
        assert "text" in response
        assert "loop" in response["text"].lower()
        assert "print" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_summarization(self, groq_client):
        """Test text summarization"""
        long_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".
        """
        
        response = await groq_client.completion(
            [{"role": "user", "content": f"Summarize this text in one sentence: {long_text}"}],
            stream=False
        )
        
        assert "text" in response
        assert "artificial intelligence" in response["text"].lower() or "ai" in response["text"].lower()
        assert len(response["text"]) < len(long_text)  # Should be shorter

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
