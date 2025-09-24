"""
Clean Streaming Test - No Debug Noise

This test shows streaming clearly without debug messages interfering.
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

    # Configure WITHOUT debug to see clean streaming
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False  # Turn off debug for clean output
    )
    client = BaseLLMClient(config, debug=False)

    print("🌊 Clean Streaming Test")
    print("=" * 50)

    # Test 1: Traditional Chat Completions streaming (clean)
    print("\n📡 Test 1: Chat Completions Streaming")
    print("🤖 Tell me a story about a robot (streaming):")
    print("📝 ", end="", flush=True)
    
    try:
        async for chunk in await client.completion(
            [{"role": "user", "content": "Tell me a very short story about a robot in exactly 3 sentences"}],
            stream=True,
            debug=False  # Explicitly disable debug
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Responses API streaming (clean)
    print("🆕 Test 2: Responses API Streaming")
    print("🤖 Count to 10 slowly (streaming):")
    print("📝 ", end="", flush=True)
    
    try:
        async for chunk in await client.completion(
            input="Count from 1 to 10, with a word between each number",
            instructions="You are a helpful assistant. Be concise.",
            stream=True,
            debug=False  # Explicitly disable debug
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Show the difference with a non-streaming call
    print("📄 Test 3: Non-streaming for comparison")
    try:
        response = await client.completion(
            [{"role": "user", "content": "Say 'Hello World' in 3 different languages"}],
            stream=False,
            debug=False
        )
        print(f"🤖 Non-streaming response: {response['text']}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ Streaming tests completed!")
    print("💡 You should see text appearing word-by-word in the streaming tests above")

if __name__ == "__main__":
    asyncio.run(main())
