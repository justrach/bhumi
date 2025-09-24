"""
Debug Responses API Conversion

Let's see exactly what happens when we call the Responses API.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def debug_responses_api():
    """Debug the Responses API conversion step by step"""
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

    print("🔍 Debug Responses API Conversion")
    print("=" * 50)

    # Test 1: Check if Responses API detection works
    print("\n📋 Step 1: Test Responses API detection")
    try:
        print("Calling completion with input= parameter...")
        
        # This should trigger Responses API mode
        result = await client.completion(
            input="Say hello world",
            stream=False,  # Start with non-streaming
            debug=True
        )
        
        print(f"✅ Non-streaming result: {result.get('text', 'No text')}")
        
    except Exception as e:
        print(f"❌ Error in non-streaming: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Check streaming
    print("\n📋 Step 2: Test Responses API streaming")
    try:
        print("Calling completion with input= and stream=True...")
        
        generator = await client.completion(
            input="Count to 3",
            stream=True,
            debug=True
        )
        
        print(f"Generator type: {type(generator)}")
        
        chunk_count = 0
        async for chunk in generator:
            chunk_count += 1
            print(f"Chunk {chunk_count}: '{chunk}'")
            if chunk_count >= 5:  # Limit output
                print("... (stopping after 5 chunks)")
                break
        
        print(f"✅ Total chunks: {chunk_count}")
        
    except Exception as e:
        print(f"❌ Error in streaming: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Compare with direct Chat Completions
    print("\n📋 Step 3: Compare with direct Chat Completions")
    try:
        print("Calling completion with messages= parameter...")
        
        generator = await client.completion(
            [{"role": "user", "content": "Count to 3"}],
            stream=True,
            debug=True
        )
        
        chunk_count = 0
        async for chunk in generator:
            chunk_count += 1
            print(f"Direct chunk {chunk_count}: '{chunk}'")
            if chunk_count >= 5:
                print("... (stopping after 5 chunks)")
                break
        
        print(f"✅ Direct Chat Completions chunks: {chunk_count}")
        
    except Exception as e:
        print(f"❌ Error in direct Chat Completions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_responses_api())
