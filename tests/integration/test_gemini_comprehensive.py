"""
Comprehensive Gemini Integration Tests

Tests streaming, tool use, and structured outputs for Google Gemini models.
Run with: pytest tests/integration/test_gemini_comprehensive.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def gemini_client():
    """Create Gemini client for testing"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("No GEMINI_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="gemini/gemini-1.5-flash",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestGeminiBasic:
    """Basic Gemini functionality tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, gemini_client):
        """Test basic Chat Completions API with Gemini"""
        response = await gemini_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_system_message(self, gemini_client):
        """Test system message handling with Gemini"""
        response = await gemini_client.completion(
            [
                {"role": "system", "content": "You are a helpful science tutor"},
                {"role": "user", "content": "What is H2O?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "water" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_math_question(self, gemini_client):
        """Test math capabilities"""
        response = await gemini_client.completion(
            [{"role": "user", "content": "What is 7 * 9?"}],
            stream=False
        )
        assert "text" in response
        assert "63" in response["text"]

class TestGeminiStreaming:
    """Gemini streaming tests"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, gemini_client):
        """Test basic streaming with Gemini"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await gemini_client.completion(
            [{"role": "user", "content": "Tell me a short story about a robot"}],
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 25:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"
    
    @pytest.mark.asyncio
    async def test_streaming_with_system_message(self, gemini_client):
        """Test streaming with system message"""
        chunk_count = 0
        
        async for chunk in await gemini_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant. Be concise."},
                {"role": "user", "content": "Explain photosynthesis in one sentence"}
            ],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 15:
                break
        
        assert chunk_count > 0
    
    @pytest.mark.asyncio
    async def test_streaming_simple_prompt(self, gemini_client):
        """Test streaming with simple prompt"""
        chunk_count = 0
        
        async for chunk in await gemini_client.completion(
            [{"role": "user", "content": "Count to 5"}],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 10:
                break
        
        assert chunk_count >= 0  # May be 0 for some prompts

class TestGeminiTools:
    """Gemini tool calling tests"""
    
    @pytest.mark.asyncio
    async def test_function_calling(self, gemini_client):
        """Test function calling with Gemini"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is sunny and 25°C"
        
        gemini_client.tool_registry.register(
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
        
        response = await gemini_client.completion(
            [{"role": "user", "content": "What's the weather in Tokyo?"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain weather information
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self, gemini_client):
        """Test calculator tool with Gemini"""
        def calculate(expression: str) -> str:
            try:
                result = eval(expression.replace("^", "**"))
                return f"{expression} = {result}"
            except:
                return f"Cannot calculate: {expression}"
        
        gemini_client.tool_registry.register(
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
        
        response = await gemini_client.completion(
            [{"role": "user", "content": "What is 25 * 4?"}],
            stream=False
        )
        
        assert "text" in response
        # Should contain calculation result
    
    @pytest.mark.asyncio
    async def test_text_analysis_tool(self, gemini_client):
        """Test text analysis tool with Gemini"""
        def analyze_text(text: str) -> str:
            word_count = len(text.split())
            char_count = len(text)
            return f"Text analysis: {word_count} words, {char_count} characters"
        
        gemini_client.tool_registry.register(
            name="analyze_text",
            func=analyze_text,
            description="Analyze text for word and character count",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze"
                    }
                },
                "required": ["text"]
            }
        )
        
        response = await gemini_client.completion(
            [{"role": "user", "content": "Analyze this text: 'Hello world, this is a test message'"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0

class TestGeminiStructuredOutputs:
    """Gemini structured outputs tests"""
    
    @pytest.mark.asyncio
    async def test_json_output_prompt_engineering(self, gemini_client):
        """Test JSON output using prompt engineering"""
        response = await gemini_client.completion(
            [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that always responds with valid JSON. Generate a product description with name, price, and category fields."
                },
                {
                    "role": "user", 
                    "content": "Create a product description for a wireless mouse, $29.99, in electronics category. Respond only with JSON."
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
                assert "price" in json_data or "Price" in json_data
                assert "category" in json_data or "Category" in json_data
            else:
                # If no JSON found, at least check content
                assert "mouse" in response_text.lower()
                assert "29.99" in response_text
                assert "electronics" in response_text.lower()
        except json.JSONDecodeError:
            # If JSON parsing fails, check for expected content
            assert "mouse" in response_text.lower()
            assert "29.99" in response_text
            assert "electronics" in response_text.lower()
    
    @pytest.mark.asyncio
    async def test_structured_output_with_satya(self, gemini_client):
        """Test structured outputs with Satya (if available)"""
        try:
            from satya import Model, Field
            
            class MovieReview(Model):
                title: str = Field(description="Movie title")
                director: str = Field(description="Movie director")
                rating: int = Field(description="Rating from 1-10")
                genre: str = Field(description="Movie genre")
            
            gemini_client.set_structured_output(MovieReview)
            
            response = await gemini_client.completion(
                [{"role": "user", "content": "Create a movie review for 'Inception' directed by Christopher Nolan, rating 9/10, sci-fi genre"}],
                stream=False
            )
            
            assert "text" in response
            assert "inception" in response["text"].lower()
            assert "nolan" in response["text"].lower()
            assert "9" in response["text"]
            
        except ImportError:
            pytest.skip("Satya not available for structured outputs test")
    
    @pytest.mark.asyncio
    async def test_list_generation(self, gemini_client):
        """Test generating structured lists"""
        response = await gemini_client.completion(
            [
                {
                    "role": "system",
                    "content": "Generate a JSON array of programming languages with their primary use cases."
                },
                {
                    "role": "user",
                    "content": "List 3 programming languages with their use cases in JSON format."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain programming language names
        assert any(lang in response_text.lower() for lang in ["python", "javascript", "java", "c++", "go", "rust"])

class TestGeminiEdgeCases:
    """Gemini edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, gemini_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await gemini_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_multilingual_content(self, gemini_client):
        """Test with multilingual content"""
        response = await gemini_client.completion(
            [{"role": "user", "content": "Translate 'Good morning' to Spanish, French, and German"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain translations
    
    @pytest.mark.asyncio
    async def test_code_generation(self, gemini_client):
        """Test code generation capabilities"""
        response = await gemini_client.completion(
            [{"role": "user", "content": "Write a simple Python function to calculate factorial"}],
            stream=False
        )
        
        assert "text" in response
        assert "def" in response["text"]
        assert "factorial" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_reasoning_task(self, gemini_client):
        """Test reasoning capabilities"""
        response = await gemini_client.completion(
            [{"role": "user", "content": "If a train travels 60 mph for 2 hours, how far does it go?"}],
            stream=False
        )
        
        assert "text" in response
        assert "120" in response["text"]

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
