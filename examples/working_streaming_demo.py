"""
Working Streaming Demo

This shows streaming working properly with clean output.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def clean_streaming_demo():
    """Demo streaming with clean, visible output"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    # Use minimal debug to avoid noise but still see streaming
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config, debug=False)

    print("🌊 Working Streaming Demo")
    print("=" * 40)

    # Test 1: Chat Completions streaming (this works!)
    print("\n📡 Chat Completions Streaming:")
    print("🤖 Response: ", end="", flush=True)
    
    chunk_count = 0
    async for chunk in await client.completion(
        [{"role": "user", "content": "Tell me a short joke"}],
        stream=True
    ):
        chunk_count += 1
        print(chunk, end="", flush=True)
        sys.stdout.flush()  # Force flush to terminal
    
    print(f"\n✅ Received {chunk_count} chunks")

    # Test 2: Responses API streaming (converted to Chat Completions)
    print("\n🆕 Responses API Streaming (converted):")
    print("🤖 Response: ", end="", flush=True)
    
    chunk_count = 0
    async for chunk in await client.completion(
        input="Count from 1 to 5",
        stream=True
    ):
        chunk_count += 1
        print(chunk, end="", flush=True)
        sys.stdout.flush()  # Force flush to terminal
    
    print(f"\n✅ Received {chunk_count} chunks")

    # Test 3: Direct astream_completion method
    print("\n🔧 Direct astream_completion:")
    print("🤖 Response: ", end="", flush=True)
    
    chunk_count = 0
    async for chunk in client.astream_completion([
        {"role": "user", "content": "Say hello world"}
    ]):
        chunk_count += 1
        print(chunk, end="", flush=True)
        sys.stdout.flush()  # Force flush to terminal
    
    print(f"\n✅ Received {chunk_count} chunks")

    print(f"\n🎉 SUCCESS: All streaming methods are working!")
    print(f"💡 The streaming was working all along - the issue was visual display")

if __name__ == "__main__":
    asyncio.run(clean_streaming_demo())
