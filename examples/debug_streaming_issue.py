"""
Debug Streaming Issue

Let's see what's happening with the Responses API streaming conversion.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config, debug=False)

    print("🔍 Debug Streaming Issue")
    print("=" * 40)

    # Test 1: Working Chat Completions streaming
    print("\n✅ Test 1: Chat Completions (should work)")
    print("Response: ", end="", flush=True)
    
    chunk_count = 0
    async for chunk in await client.completion(
        [{"role": "user", "content": "Count: 1, 2, 3"}],
        stream=True
    ):
        chunk_count += 1
        print(f"[{chunk}]", end="", flush=True)
    print(f"\n📊 Received {chunk_count} chunks")

    # Test 2: Responses API streaming (problematic)
    print("\n❓ Test 2: Responses API (might be empty)")
    print("Response: ", end="", flush=True)
    
    chunk_count = 0
    try:
        async for chunk in await client.completion(
            input="Count: 1, 2, 3",
            stream=True,
            debug=True  # Enable debug just for this call
        ):
            chunk_count += 1
            print(f"[{chunk}]", end="", flush=True)
        print(f"\n📊 Received {chunk_count} chunks")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    # Test 3: Let's try a simpler Responses API call
    print("\n🔧 Test 3: Simple Responses API non-streaming")
    try:
        response = await client.completion(
            input="Say hello",
            debug=True
        )
        print(f"✅ Response: {response.get('text', 'No text found')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
