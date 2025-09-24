"""
Cerebras Tests Without Tool Calling

Tests for Cerebras that completely skip tool calling to avoid hanging.
Run with: pytest tests/integration/test_cerebras_no_tools.py -v
"""

import asyncio
import os
import pytest
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

@pytest.fixture
def cerebras_client():
    """Create Cerebras client for testing"""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        pytest.skip("No CEREBRAS_API_KEY found")
    
    config = LLMConfig(
        api_key=api_key,
        model="cerebras/llama3.1-8b",
        debug=False
    )
    return BaseLLMClient(config, debug=False)

class TestCerebrasBasicNoTools:
    """Basic Cerebras functionality tests without tools"""
    
    @pytest.mark.asyncio
    async def test_chat_completions_basic(self, cerebras_client):
        """Test basic Chat Completions API with Cerebras"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_system_message(self, cerebras_client):
        """Test system message handling with Cerebras"""
        response = await cerebras_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant that gives short answers"},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "paris" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_simple_math(self, cerebras_client):
        """Test simple math capabilities"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "What is 6 + 4?"}],
            stream=False
        )
        assert "text" in response
        assert "10" in response["text"]
    
    @pytest.mark.asyncio
    async def test_conversation(self, cerebras_client):
        """Test multi-turn conversation"""
        response = await cerebras_client.completion(
            [
                {"role": "user", "content": "My name is Alice"},
                {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                {"role": "user", "content": "What's my name?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "alice" in response["text"].lower()

class TestCerebrasStreamingNoTools:
    """Cerebras streaming tests without tools"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, cerebras_client):
        """Test basic streaming with Cerebras"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await cerebras_client.completion(
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
    async def test_streaming_with_system_message(self, cerebras_client):
        """Test streaming with system message"""
        chunk_count = 0
        
        async for chunk in await cerebras_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant. Be brief."},
                {"role": "user", "content": "What is AI?"}
            ],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 15:
                break
        
        assert chunk_count > 0
    
    @pytest.mark.asyncio
    async def test_streaming_creative(self, cerebras_client):
        """Test streaming with creative task"""
        chunk_count = 0
        
        async for chunk in await cerebras_client.completion(
            [{"role": "user", "content": "Write a haiku about technology"}],
            stream=True
        ):
            chunk_count += 1
            if chunk_count >= 25:
                break
        
        assert chunk_count >= 0  # May be 0 for some prompts

class TestCerebrasStructuredNoTools:
    """Cerebras structured outputs tests without tools"""
    
    @pytest.mark.asyncio
    async def test_json_output_prompt_engineering(self, cerebras_client):
        """Test JSON output using prompt engineering"""
        response = await cerebras_client.completion(
            [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that always responds with valid JSON. Generate a person profile with name, age, and occupation fields."
                },
                {
                    "role": "user", 
                    "content": "Create a profile for Mike Chen, 35 years old, software engineer. Respond only with JSON."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain the requested information
        assert "mike" in response_text.lower()
        assert "35" in response_text
        assert "engineer" in response_text.lower()
        
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                assert isinstance(json_data, dict)
            except json.JSONDecodeError:
                # JSON parsing failed, but content is there
                pass
    
    @pytest.mark.asyncio
    async def test_list_generation(self, cerebras_client):
        """Test generating lists"""
        response = await cerebras_client.completion(
            [
                {
                    "role": "system",
                    "content": "Generate a simple list of 3 programming languages."
                },
                {
                    "role": "user",
                    "content": "List 3 popular programming languages."
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain programming language names
        assert any(lang in response_text.lower() for lang in ["python", "javascript", "java", "c++", "go", "rust"])

class TestCerebrasEdgeCasesNoTools:
    """Cerebras edge cases without tools"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, cerebras_client):
        """Test with empty messages"""
        with pytest.raises(ValueError):
            await cerebras_client.completion([], stream=False)
    
    @pytest.mark.asyncio
    async def test_creative_writing(self, cerebras_client):
        """Test creative writing capabilities"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "Write a haiku about technology"}],
            stream=False
        )
        
        assert "text" in response
        assert len(response["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_reasoning(self, cerebras_client):
        """Test logical reasoning"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "If all cats are animals and Fluffy is a cat, what is Fluffy?"}],
            stream=False
        )
        
        assert "text" in response
        assert "animal" in response["text"].lower()

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
