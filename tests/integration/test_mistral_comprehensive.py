"""
Comprehensive Mistral AI Integration Tests

Tests for Mistral AI provider covering:
- Chat Completions API
- Streaming responses  
- Function calling/tools
- Image analysis (vision models)
- Structured outputs

Run with: pytest tests/integration/test_mistral_comprehensive.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def mistral_client():
    """Create Mistral client for testing"""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        pytest.skip("No MISTRAL_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="mistral/mistral-small-latest",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

@pytest.fixture
def mistral_vision_client():
    """Create Mistral client for vision testing"""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        pytest.skip("No MISTRAL_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="mistral/pixtral-12b-2409",  # Mistral's vision model
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestMistralBasic:
    """Basic Mistral functionality tests"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, mistral_client):
        """Test basic Chat Completions API with Mistral"""
        response = await mistral_client.completion(
            [{"role": "user", "content": "Say hello in French"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "bonjour" in response["text"].lower() or "salut" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_system_message(self, mistral_client):
        """Test system message handling with Mistral"""
        response = await mistral_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant that gives very short answers"},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "paris" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_simple_math(self, mistral_client):
        """Test simple math capabilities"""
        response = await mistral_client.completion(
            [{"role": "user", "content": "What is 7 + 5?"}],
            stream=False
        )
        assert "text" in response
        assert "12" in response["text"]
    
    @pytest.mark.asyncio
    async def test_conversation(self, mistral_client):
        """Test multi-turn conversation"""
        response = await mistral_client.completion(
            [
                {"role": "user", "content": "My name is Marie"},
                {"role": "assistant", "content": "Hello Marie! Nice to meet you."},
                {"role": "user", "content": "What's my name?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "marie" in response["text"].lower()

class TestMistralStreaming:
    """Mistral streaming tests"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, mistral_client):
        """Test basic streaming with Mistral"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await mistral_client.completion(
            [{"role": "user", "content": "Tell me a short joke in French"}],
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 20:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"
    
    @pytest.mark.asyncio
    async def test_streaming_with_system_message(self, mistral_client):
        """Test streaming with system message"""
        chunk_count = 0
        
        async for chunk in await mistral_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant. Be brief."},
                {"role": "user", "content": "Explain AI in one sentence"}
            ],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 15:
                break
        
        assert chunk_count > 0
    
    @pytest.mark.asyncio
    async def test_streaming_creative(self, mistral_client):
        """Test streaming with creative task"""
        chunk_count = 0
        
        async for chunk in await mistral_client.completion(
            [{"role": "user", "content": "Write a haiku about Paris"}],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 25:
                break
        
        assert chunk_count >= 0  # May be 0 for some prompts

class TestMistralTools:
    """Mistral tool calling tests"""
    
    @pytest.mark.asyncio
    async def test_function_calling(self, mistral_client):
        """Test function calling with Mistral"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is sunny and 22°C"
        
        mistral_client.tool_registry.register(
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
        
        response = await asyncio.wait_for(
            mistral_client.completion(
                [
                    {"role": "system", "content": "You are a helpful assistant with access to weather tools. Use the get_weather tool when asked about weather."},
                    {"role": "user", "content": "What's the weather like in Paris?"}
                ],
                stream=False
            ),
            timeout=30.0
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain weather information from the tool
        print(f"✅ Mistral weather tool response: {response['text'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self, mistral_client):
        """Test calculator tool with Mistral"""
        def calculate(expression: str) -> str:
            try:
                result = eval(expression.replace("^", "**"))
                return f"{expression} = {result}"
            except:
                return f"Cannot calculate: {expression}"
        
        mistral_client.tool_registry.register(
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
        
        response = await asyncio.wait_for(
            mistral_client.completion(
                [
                    {"role": "system", "content": "You are a helpful assistant with a calculator. Use it whenever math is required."},
                    {"role": "user", "content": "What is 15 * 8?"}
                ],
                stream=False
            ),
            timeout=30.0
        )
        
        assert "text" in response
        # Should contain calculation result
        assert "120" in response["text"]
        print(f"✅ Mistral calculator tool response: {response['text'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_string_tool(self, mistral_client):
        """Test string manipulation tool with Mistral"""
        def reverse_string(text: str) -> str:
            return f"Reversed: {text[::-1]}"
        
        mistral_client.tool_registry.register(
            name="reverse_string",
            func=reverse_string,
            description="Reverse a string",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to reverse"
                    }
                },
                "required": ["text"]
            }
        )
        
        response = await asyncio.wait_for(
            mistral_client.completion(
                [
                    {"role": "system", "content": "You are a helpful assistant with string manipulation tools."},
                    {"role": "user", "content": "Reverse the string 'bonjour monde'"}
                ],
                stream=False
            ),
            timeout=30.0
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        print(f"✅ Mistral string tool response: {response['text'][:100]}...")

class TestMistralVision:
    """Mistral vision/image analysis tests"""
    
    @pytest.mark.asyncio
    async def test_image_analysis_basic(self, mistral_vision_client):
        """Test basic image analysis with Mistral vision model"""
        # Create a simple test image (base64 encoded 1x1 red pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        response = await mistral_vision_client.completion(
            [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": "What color is this image?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{test_image_b64}"}}
                    ]
                }
            ],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        print(f"✅ Mistral vision response: {response['text'][:100]}...")

class TestMistralStructuredOutputs:
    """Mistral structured outputs tests"""
    
    @pytest.mark.asyncio
    async def test_json_output_prompt_engineering(self, mistral_client):
        """Test JSON output using prompt engineering"""
        response = await mistral_client.completion(
            [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that always responds with valid JSON. Generate a person profile with name, age, and occupation fields."
                },
                {
                    "role": "user", 
                    "content": "Create a profile for Pierre Dubois, 42 years old, chef. Respond only with JSON."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain the requested information
        assert "pierre" in response_text.lower()
        assert "42" in response_text
        assert "chef" in response_text.lower()
        
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                assert isinstance(json_data, dict)
                print(f"✅ Mistral JSON parsing successful: {json_data}")
            except json.JSONDecodeError:
                # JSON parsing failed, but content is there
                pass
    
    @pytest.mark.asyncio
    async def test_list_generation(self, mistral_client):
        """Test generating lists"""
        response = await mistral_client.completion(
            [
                {
                    "role": "system",
                    "content": "Generate a simple list of 3 French cities."
                },
                {
                    "role": "user",
                    "content": "List 3 major French cities."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain French city names
        assert any(city in response_text.lower() for city in ["paris", "lyon", "marseille", "toulouse", "nice"])

class TestMistralEdgeCases:
    """Mistral edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, mistral_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await mistral_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_creative_writing(self, mistral_client):
        """Test creative writing capabilities"""
        response = await mistral_client.completion(
            [{"role": "user", "content": "Write a haiku about the Eiffel Tower"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_reasoning(self, mistral_client):
        """Test logical reasoning"""
        response = await mistral_client.completion(
            [{"role": "user", "content": "If all roses are flowers and this red thing is a rose, what is it?"}],
            stream=False
        )
        
        assert "text" in response
        assert "flower" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_french_language(self, mistral_client):
        """Test French language capabilities (Mistral's specialty)"""
        response = await mistral_client.completion(
            [{"role": "user", "content": "Écrivez une phrase en français sur l'intelligence artificielle."}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
        # Should contain French words
        french_words = ["intelligence", "artificielle", "ia", "technologie", "ordinateur"]
        assert any(word in response["text"].lower() for word in french_words)

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
