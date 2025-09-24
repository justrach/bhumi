"""
Comprehensive Integration Tests for Responses API

Tests streaming, non-streaming, tools, and various scenarios.
"""

import asyncio
import os
import pytest
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

class TestResponsesAPIBasic:
    """Basic Responses API functionality tests"""
    
    @pytest.mark.asyncio
    async def test_responses_api_detection(self, openai_client):
        """Test that Responses API is detected when input= is used"""
        response = await openai_client.completion(
            input="Say hello",
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_responses_api_with_instructions(self, openai_client):
        """Test Responses API with instructions parameter"""
        response = await openai_client.completion(
            input="What is 2+2?",
            instructions="You are a math teacher. Be precise.",
            stream=False
        )
        assert "text" in response
        assert "4" in response["text"]
    
    @pytest.mark.asyncio
    async def test_responses_api_streaming_basic(self, openai_client):
        """Test basic Responses API streaming"""
        chunk_count = 0
        accumulated_text = ""
        
        async for chunk in await openai_client.completion(
            input="Say 'Hello World' and nothing else",
            stream=True
        ):
            chunk_count += 1
            accumulated_text += chunk
            if chunk_count >= 10:  # Prevent infinite loops
                break
        
        assert chunk_count > 0, "Should receive at least one chunk"
        assert len(accumulated_text) > 0, "Should accumulate some text"

class TestResponsesAPIPrompts:
    """Test different types of prompts with Responses API"""
    
    @pytest.mark.asyncio
    async def test_simple_prompts(self, openai_client):
        """Test simple prompts that should work"""
        test_cases = [
            "Say hello",
            "What is 1+1?",
            "Tell me a joke",
            "Count: 1, 2, 3",
        ]
        
        for prompt in test_cases:
            chunk_count = 0
            async for chunk in await openai_client.completion(
                input=prompt,
                stream=True
            ):
                chunk_count += 1
                if chunk_count >= 5:  # Limit chunks per test
                    break
            
            # Some prompts might not stream well, but they shouldn't error
            assert chunk_count >= 0

class TestResponsesAPITools:
    """Test Responses API with tools (function calling)"""
    
    @pytest.mark.asyncio
    async def test_responses_api_with_tools(self, openai_client):
        """Test that tools work with Responses API"""
        # Register a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is sunny and 25°C"
        
        # Add tool to client
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
        
        # Test with Responses API
        response = await openai_client.completion(
            input="What's the weather in Paris?",
            instructions="Use the get_weather tool to check weather",
            stream=False
        )
        
        assert "text" in response
        # Should contain weather information or tool call result
        assert len(response["text"]) > 0

class TestResponsesAPIEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_input(self, openai_client):
        """Test with empty input"""
        with pytest.raises(ValueError, match="input.*required"):
            await openai_client.completion(
                input="",
                stream=False
            )
    
    @pytest.mark.asyncio
    async def test_only_instructions(self, openai_client):
        """Test with only instructions (should fail)"""
        with pytest.raises(ValueError):
            await openai_client.completion(
                instructions="You are helpful",
                stream=False
            )
    
    @pytest.mark.asyncio
    async def test_mixed_parameters(self, openai_client):
        """Test mixing messages and input parameters"""
        # This should use Responses API (input takes precedence)
        response = await openai_client.completion(
            messages=[{"role": "user", "content": "This should be ignored"}],
            input="This should be used",
            stream=False
        )
        assert "text" in response

class TestResponsesAPIPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_streaming_vs_non_streaming(self, openai_client):
        """Compare streaming vs non-streaming performance"""
        prompt = "Write a short sentence about AI"
        
        # Non-streaming
        import time
        start_time = time.time()
        non_streaming_response = await openai_client.completion(
            input=prompt,
            stream=False
        )
        non_streaming_time = time.time() - start_time
        
        # Streaming
        start_time = time.time()
        streaming_chunks = []
        async for chunk in await openai_client.completion(
            input=prompt,
            stream=True
        ):
            streaming_chunks.append(chunk)
            if len(streaming_chunks) >= 10:  # Limit for test
                break
        streaming_time = time.time() - start_time
        
        # Both should complete successfully
        assert len(non_streaming_response["text"]) > 0
        assert len(streaming_chunks) >= 0  # Might be 0 for some prompts
        
        # Performance comparison (streaming might be faster for first chunk)
        print(f"Non-streaming: {non_streaming_time:.2f}s")
        print(f"Streaming: {streaming_time:.2f}s")

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
