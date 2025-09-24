"""
Minimal Streaming Test

Test both methods side by side to see the difference.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def test_direct_streaming():
    """Test direct Chat Completions streaming"""
    print("🔵 Direct Chat Completions Streaming:")
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config, debug=False)
    
    print("Response: ", end="", flush=True)
    chunk_count = 0
    
    async for chunk in await client.completion(
        [{"role": "user", "content": "Count: 1, 2, 3, 4, 5"}],
        stream=True
    ):
        chunk_count += 1
        print(chunk, end="", flush=True)
    
    print(f"\n✅ Direct streaming: {chunk_count} chunks")
    return chunk_count

async def test_responses_api_streaming():
    """Test Responses API streaming (converted)"""
    print("\n🟡 Responses API Streaming (converted):")
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config, debug=False)
    
    print("Response: ", end="", flush=True)
    chunk_count = 0
    
    # This should trigger Responses API mode and convert to Chat Completions
    stream_generator = await client.completion(
        input="Count: 1, 2, 3, 4, 5",
        stream=True
    )
    
    print(f"\nGenerator type: {type(stream_generator)}")
    
    async for chunk in stream_generator:
        chunk_count += 1
        print(chunk, end="", flush=True)
    
    print(f"\n✅ Responses API streaming: {chunk_count} chunks")
    return chunk_count

async def main():
    print("🧪 Minimal Streaming Comparison")
    print("=" * 40)
    
    # Test both methods
    direct_chunks = await test_direct_streaming()
    responses_chunks = await test_responses_api_streaming()
    
    print(f"\n📊 Results:")
    print(f"   Direct Chat Completions: {direct_chunks} chunks")
    print(f"   Responses API (converted): {responses_chunks} chunks")
    
    if responses_chunks == 0:
        print("❌ Responses API streaming is not working")
    elif responses_chunks > 0:
        print("✅ Responses API streaming is working!")
    else:
        print("❓ Unexpected result")

if __name__ == "__main__":
    asyncio.run(main())
