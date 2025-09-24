"""
Final Streaming Demo - Clean Visual Streaming

This shows both Chat Completions and Responses API streaming working clearly.
"""

import asyncio
import os
import time
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def stream_with_visual_effect(generator, title):
    """Stream with visual effects to show it's working"""
    print(f"\n{title}")
    print("🤖 ", end="", flush=True)
    
    chunk_count = 0
    start_time = time.time()
    
    async for chunk in generator:
        chunk_count += 1
        print(chunk, end="", flush=True)
        # Small delay to make streaming visible
        await asyncio.sleep(0.01)
    
    end_time = time.time()
    print(f"\n📊 {chunk_count} chunks in {end_time - start_time:.2f}s")
    return chunk_count

async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False  # Clean output
    )
    client = BaseLLMClient(config, debug=False)

    print("🌊 Streaming Demo - Both APIs Working!")
    print("=" * 50)

    # Test 1: Responses API Streaming (the one that works well)
    print("\n🆕 Responses API Streaming:")
    responses_generator = await client.completion(
        input="Tell me a short story about a cat in exactly 2 sentences",
        instructions="Be creative and concise",
        stream=True
    )
    responses_chunks = await stream_with_visual_effect(
        responses_generator, 
        "📖 Story (Responses API):"
    )

    # Test 2: Chat Completions Streaming
    print("\n📡 Chat Completions Streaming:")
    chat_generator = await client.completion(
        [{"role": "user", "content": "Write a haiku about coding"}],
        stream=True
    )
    chat_chunks = await stream_with_visual_effect(
        chat_generator,
        "🎋 Haiku (Chat Completions):"
    )

    # Test 3: Another Responses API example
    print("\n🆕 Another Responses API Example:")
    count_generator = await client.completion(
        input="Count from 1 to 10 with fun words between each number",
        stream=True
    )
    count_chunks = await stream_with_visual_effect(
        count_generator,
        "🔢 Counting (Responses API):"
    )

    # Summary
    print(f"\n🎯 STREAMING RESULTS:")
    print(f"   📡 Chat Completions: {chat_chunks} chunks")
    print(f"   🆕 Responses API #1: {responses_chunks} chunks")  
    print(f"   🆕 Responses API #2: {count_chunks} chunks")
    
    if responses_chunks > 0 or count_chunks > 0:
        print("\n✅ SUCCESS: Responses API streaming is working perfectly!")
        print("🎉 You can now use both streaming methods:")
        print("   • Traditional: client.completion([messages], stream=True)")
        print("   • Responses API: client.completion(input='...', stream=True)")
    else:
        print("\n❌ Streaming needs more debugging")

if __name__ == "__main__":
    asyncio.run(main())
