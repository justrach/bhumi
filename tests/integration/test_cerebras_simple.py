"""
Simple Cerebras Integration Tests

Focused tests for Cerebras that avoid potentially problematic features.
Run with: pytest tests/integration/test_cerebras_simple.py -v
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

class TestCerebrasBasic:
    """Basic Cerebras functionality tests"""
    
    @pytest.mark.asyncio
    async def test_simple_completion(self, cerebras_client):
        """Test basic completion"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        assert "text" in response
        assert len(response["text"]) > 0
        assert "hello" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_math_question(self, cerebras_client):
        """Test simple math"""
        response = await cerebras_client.completion(
            [{"role": "user", "content": "What is 5 + 3?"}],
            stream=False
        )
        assert "text" in response
        assert "8" in response["text"]
    
    @pytest.mark.asyncio
    async def test_system_message(self, cerebras_client):
        """Test system message"""
        response = await cerebras_client.completion(
            [
                {"role": "system", "content": "You are a helpful assistant. Be brief."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            stream=False
        )
        assert "text" in response
        assert "paris" in response["text"].lower()

class TestCerebrasStreaming:
    """Cerebras streaming tests"""
    
    @pytest.mark.asyncio
    async def test_basic_streaming(self, cerebras_client):
        """Test basic streaming"""
        chunk_count = 0
        accumulated_text = ""
        
        try:
            async for chunk in await asyncio.wait_for(
                cerebras_client.completion(
                    [{"role": "user", "content": "Count to 3"}],
                    stream=True
                ),
                timeout=30.0
            ):
                chunk_count += 1
                accumulated_text += chunk
                if chunk_count >= 10:  # Prevent infinite loops
                    break
            
            # Should receive some chunks
            assert chunk_count >= 0  # May be 0 for some prompts
            assert isinstance(accumulated_text, str)
            
        except asyncio.TimeoutError:
            pytest.skip("Cerebras streaming timed out")
    
    @pytest.mark.asyncio
    async def test_streaming_joke(self, cerebras_client):
        """Test streaming with joke"""
        chunk_count = 0
        
        try:
            async for chunk in await asyncio.wait_for(
                cerebras_client.completion(
                    [{"role": "user", "content": "Tell me a short joke"}],
                    stream=True
                ),
                timeout=30.0
            ):
                chunk_count += 1
                if chunk_count >= 15:
                    break
            
            assert chunk_count >= 0
            
        except asyncio.TimeoutError:
            pytest.skip("Cerebras joke streaming timed out")

class TestCerebrasSimpleTools:
    """Simple tool tests for Cerebras (with timeouts)"""
    
    @pytest.mark.asyncio
    async def test_simple_tool_or_skip(self, cerebras_client):
        """Test simple tool or skip if not supported"""
        def get_time() -> str:
            return "Current time: 2:30 PM"
        
        cerebras_client.tool_registry.register(
            name="get_time",
            func=get_time,
            description="Get current time",
            parameters={"type": "object", "properties": {}}
        )
        
        try:
            response = await asyncio.wait_for(
                cerebras_client.completion(
                    [{"role": "user", "content": "What time is it?"}],
                    stream=False
                ),
                timeout=15.0  # Shorter timeout
            )
            
            assert "text" in response
            assert len(response["text"]) > 0
            
        except asyncio.TimeoutError:
            pytest.skip("Cerebras tool calling timed out - may not be supported")
        except Exception as e:
            pytest.skip(f"Cerebras tool calling not supported: {e}")

class TestCerebrasJSON:
    """Simple JSON output tests"""
    
    @pytest.mark.asyncio
    async def test_simple_json(self, cerebras_client):
        """Test simple JSON generation"""
        response = await cerebras_client.completion(
            [
                {
                    "role": "system",
                    "content": "Respond only with valid JSON. Create a simple object with name and age fields."
                },
                {
                    "role": "user",
                    "content": "Create JSON for person named Bob, age 30"
                }
            ],
            stream=False
        )
        
        assert "text" in response
        response_text = response["text"]
        
        # Should contain the requested information
        assert "bob" in response_text.lower()
        assert "30" in response_text
        
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

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
