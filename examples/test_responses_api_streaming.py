"""
Test OpenAI Responses API Streaming

Simple test to verify that the new Responses API parameters work with streaming.
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
        debug=True
    )
    client = BaseLLMClient(config)

    print("🚀 Testing OpenAI Responses API Streaming")
    print("=" * 50)

    # Test 1: Traditional Chat Completions streaming
    print("\n📡 Test 1: Traditional Chat Completions streaming")
    print("Response: ", end="", flush=True)
    async for chunk in await client.completion(
        [{"role": "user", "content": "Count to 3"}],
        stream=True
    ):
        print(chunk, end="", flush=True)
    print("\n")

    # Test 2: New Responses API streaming (converted to Chat Completions)
    print("🆕 Test 2: Responses API streaming (with conversion)")
    print("Response: ", end="", flush=True)
    async for chunk in await client.completion(
        input="Count to 3",
        instructions="You are a helpful assistant",
        stream=True
    ):
        print(chunk, end="", flush=True)
    print("\n")

    # Test 3: Responses API non-streaming
    print("🆕 Test 3: Responses API non-streaming")
    response = await client.completion(
        input="Tell me a short joke",
        instructions="You are a funny assistant"
    )
    print(f"Response: {response['text']}")

    print("\n✅ All tests completed!")
    print("🎉 Responses API streaming is now working via Chat Completions conversion!")

if __name__ == "__main__":
    asyncio.run(main())
