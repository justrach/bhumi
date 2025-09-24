"""
Debug Count Issue

Let's see why some prompts work for streaming and others don't.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def debug_different_prompts():
    """Test different prompts to see which ones stream well"""
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

    print("🔍 Testing Different Prompts for Streaming")
    print("=" * 50)

    test_prompts = [
        "Count from 1 to 5, one number per line",
        "Count to 5 slowly with words between numbers",
        "List the numbers 1, 2, 3, 4, 5 with explanations",
        "Tell me a short story about counting to 5",
        "Write the numbers one through five",
        "Say hello and then count to 3"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📋 Test {i}: '{prompt}'")
        print("Response: ", end="", flush=True)
        
        chunk_count = 0
        try:
            async for chunk in await client.completion(
                input=prompt,
                stream=True
            ):
                chunk_count += 1
                print(chunk, end="", flush=True)
                if chunk_count >= 20:  # Limit to avoid too much output
                    print("... (truncated)")
                    break
            
            print(f"\n✅ Chunks: {chunk_count}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_different_prompts())
