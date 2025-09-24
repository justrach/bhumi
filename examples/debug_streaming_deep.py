"""
Deep Debug Streaming Issue

Let's find out exactly what's happening with the streaming.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def debug_streaming_step_by_step():
    """Debug streaming step by step"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=True  # Enable debug to see what's happening
    )
    client = BaseLLMClient(config, debug=True)

    print("🔍 Deep Debug: Step-by-step streaming analysis")
    print("=" * 60)

    # Test 1: Check if we get a generator
    print("\n📋 Step 1: Check generator creation")
    try:
        generator = await client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=True
        )
        print(f"✅ Generator created: {type(generator)}")
        print(f"   Is async generator: {hasattr(generator, '__aiter__')}")
        
        # Try to iterate
        print("\n📋 Step 2: Try to iterate generator")
        chunk_count = 0
        async for chunk in generator:
            chunk_count += 1
            print(f"   Chunk {chunk_count}: '{chunk}'")
            if chunk_count >= 5:  # Limit to first 5 chunks
                print("   ... (stopping after 5 chunks)")
                break
        
        print(f"✅ Total chunks received: {chunk_count}")
        
    except Exception as e:
        print(f"❌ Error in streaming: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Check non-streaming for comparison
    print("\n📋 Step 3: Check non-streaming (for comparison)")
    try:
        response = await client.completion(
            [{"role": "user", "content": "Say hello"}],
            stream=False
        )
        print(f"✅ Non-streaming response: {response.get('text', 'No text')[:100]}...")
    except Exception as e:
        print(f"❌ Error in non-streaming: {e}")

    # Test 3: Check the astream_completion method directly
    print("\n📋 Step 4: Test astream_completion directly")
    try:
        direct_generator = client.astream_completion([{"role": "user", "content": "Count to 3"}])
        print(f"✅ Direct generator created: {type(direct_generator)}")
        
        chunk_count = 0
        async for chunk in direct_generator:
            chunk_count += 1
            print(f"   Direct chunk {chunk_count}: '{chunk}'")
            if chunk_count >= 5:
                print("   ... (stopping after 5 chunks)")
                break
        
        print(f"✅ Direct streaming chunks: {chunk_count}")
        
    except Exception as e:
        print(f"❌ Error in direct streaming: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_streaming_step_by_step())
