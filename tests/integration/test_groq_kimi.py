#!/usr/bin/env python3
"""
Specific test for Groq Kimi model with provided credentials
Tests the moonshotai/kimi-k2-instruct model functionality
"""
import asyncio
import os
import sys
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bhumi.base_client import BaseLLMClient, LLMConfig

# Groq Kimi configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "groq/moonshotai/kimi-k2-instruct"

async def test_groq_kimi_basic():
    """Test basic Groq Kimi functionality"""
    print("🤖 Testing Groq Kimi Model")
    print("=" * 50)
    
    config = LLMConfig(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        debug=False  # Changed to False for cleaner output
    )
    
    print(f"Model: {config.model}")
    print(f"Provider: {config.provider}")
    print(f"Base URL: {config.base_url}")
    
    if config.base_url != "https://api.groq.com/openai/v1":
        print("❌ Base URL is incorrect!")
        return False
    
    print("✅ Configuration looks good!")
    
    try:
        client = BaseLLMClient(config, max_concurrent=1, debug=False)  # Changed to False
        
        print("\n🧪 Testing simple completion...")
        start_time = time.time()
        
        response = await client.completion([
            {"role": "user", "content": "Hello! What's your name and what can you help me with?"}
        ])
        
        end_time = time.time()
        
        if isinstance(response, dict) and 'text' in response:
            print(f"✅ Groq Kimi response successful!")
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Response preview: {response['text'][:200]}...")
            return True
        else:
            print(f"❌ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Groq Kimi test failed: {str(e)}")
        return False

async def test_groq_kimi_streaming():
    """Test Groq Kimi streaming functionality"""
    print("\n🌊 Testing Groq Kimi Streaming")
    print("=" * 40)
    
    config = LLMConfig(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        debug=False  # Less verbose for streaming
    )
    
    try:
        client = BaseLLMClient(config, max_concurrent=1)
        
        print("Starting streaming request...")
        print("Response: ", end="", flush=True)
        
        start_time = time.time()
        chunk_count = 0
        
        stream = await client.completion([
            {"role": "user", "content": "Please count from 1 to 5, with each number on a separate line. Keep it simple."}
        ], stream=True)
        
        async for chunk in stream:
            print(chunk, end="", flush=True)
            chunk_count += 1
            if chunk_count > 50:  # Prevent runaway streams
                break
                
        end_time = time.time()
        
        print(f"\n✅ Groq Kimi streaming successful!")
        print(f"Chunks received: {chunk_count}")
        print(f"Streaming time: {end_time - start_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ Groq Kimi streaming failed: {str(e)}")
        return False

async def test_groq_kimi_complex():
    """Test Groq Kimi with a more complex request"""
    print("\n🧠 Testing Groq Kimi Complex Query")
    print("=" * 40)
    
    config = LLMConfig(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        debug=False
    )
    
    try:
        client = BaseLLMClient(config, max_concurrent=1)
        
        print("Testing complex reasoning...")
        start_time = time.time()
        
        response = await client.completion([
            {"role": "user", "content": "Explain the concept of machine learning in simple terms, and give me one practical example."}
        ])
        
        end_time = time.time()
        
        if isinstance(response, dict) and 'text' in response:
            response_text = response['text']
            print(f"✅ Complex query successful!")
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Response length: {len(response_text)} characters")
            print(f"\nResponse:\n{response_text}")
            return True
        else:
            print(f"❌ Unexpected response format")
            return False
            
    except Exception as e:
        print(f"❌ Complex query failed: {str(e)}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Groq Kimi Model Test Suite")
    print("=" * 60)
    print(f"Testing model: {GROQ_MODEL}")
    print(f"API endpoint: https://api.groq.com/openai/v1")
    
    results = []
    
    # Test basic functionality
    basic_success = await test_groq_kimi_basic()
    results.append(("Basic", basic_success))
    
    # Test streaming if basic works
    streaming_success = False
    if basic_success:
        streaming_success = await test_groq_kimi_streaming()
        results.append(("Streaming", streaming_success))
    
    # Test complex query if basic works
    complex_success = False
    if basic_success:
        complex_success = await test_groq_kimi_complex()
        results.append(("Complex", complex_success))
    
    # Summary
    print(f"\n📊 Test Results")
    print("=" * 30)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nOverall: {successful_tests}/{total_tests} tests passed")
    
    if basic_success:
        print("\n🎉 Groq Kimi model is working!")
        if streaming_success and complex_success:
            print("🌟 All functionality tests passed - ready for production use!")
        elif streaming_success:
            print("✅ Basic and streaming work - complex queries may have issues")
        else:
            print("⚠️  Basic functionality works but streaming may have issues")
    else:
        print("\n❌ Groq Kimi model has configuration or connectivity issues")
        print("   Check the API key, model name, and network connectivity")
    
    return basic_success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1) 