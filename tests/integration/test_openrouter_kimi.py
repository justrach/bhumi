#!/usr/bin/env python3
"""
Test for OpenRouter Kimi model - moonshotai/kimi-k2
Tests the OpenRouter API with Moonshot AI's Kimi model
"""
import asyncio
import os
import sys
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bhumi.base_client import BaseLLMClient, LLMConfig

# OpenRouter Kimi configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openrouter/moonshotai/kimi-k2"

async def test_openrouter_kimi_basic():
    """Test basic OpenRouter Kimi functionality"""
    print("🚀 Testing OpenRouter Kimi Model")
    print("=" * 50)
    
    config = LLMConfig(
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
        debug=False  # Changed to False for cleaner output
    )
    
    print(f"Model: {config.model}")
    print(f"Provider: {config.provider}")
    print(f"Base URL: {config.base_url}")
    
    if config.base_url != "https://openrouter.ai/api/v1":
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
            print(f"✅ OpenRouter Kimi response successful!")
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Response preview: {response['text'][:200]}...")
            return True
        else:
            print(f"❌ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter Kimi test failed: {str(e)}")
        return False

async def test_openrouter_kimi_streaming():
    """Test OpenRouter Kimi streaming functionality"""
    print("\n🌊 Testing OpenRouter Kimi Streaming")
    print("=" * 40)
    
    config = LLMConfig(
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
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
        
        print(f"\n✅ OpenRouter Kimi streaming successful!")
        print(f"Chunks received: {chunk_count}")
        print(f"Streaming time: {end_time - start_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter Kimi streaming failed: {str(e)}")
        return False

async def test_openrouter_kimi_complex():
    """Test OpenRouter Kimi with a more complex request"""
    print("\n🧠 Testing OpenRouter Kimi Complex Query")
    print("=" * 40)
    
    config = LLMConfig(
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
        debug=False
    )
    
    try:
        client = BaseLLMClient(config, max_concurrent=1)
        
        print("Testing complex reasoning...")
        start_time = time.time()
        
        response = await client.completion([
            {"role": "user", "content": "Compare the advantages and disadvantages of Python vs JavaScript for web development. Give me 3 key points for each."}
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

async def test_openrouter_comparison():
    """Compare OpenRouter vs Groq for the same query"""
    print("\n⚖️ Testing OpenRouter vs Groq Comparison")
    print("=" * 40)
    
    test_query = "What is artificial intelligence in one sentence?"
    
    # Test OpenRouter
    print("🚀 OpenRouter Response:")
    try:
        or_config = LLMConfig(api_key=OPENROUTER_API_KEY, model=OPENROUTER_MODEL, debug=False)
        or_client = BaseLLMClient(or_config, max_concurrent=1)
        
        or_start = time.time()
        or_response = await or_client.completion([{"role": "user", "content": test_query}])
        or_time = time.time() - or_start
        
        if isinstance(or_response, dict) and 'text' in or_response:
            print(f"✅ OpenRouter: {or_response['text'][:150]}... ({or_time:.2f}s)")
            or_success = True
        else:
            print(f"❌ OpenRouter failed")
            or_success = False
    except Exception as e:
        print(f"❌ OpenRouter error: {e}")
        or_success = False
    
    # Test Groq for comparison
    print("\n⚡ Groq Response:")
    try:
        groq_config = LLMConfig(
            api_key=os.environ.get("GROQ_API_KEY"), 
            model="groq/moonshotai/kimi-k2-instruct", 
            debug=False
        )
        groq_client = BaseLLMClient(groq_config, max_concurrent=1)
        
        groq_start = time.time()
        groq_response = await groq_client.completion([{"role": "user", "content": test_query}])
        groq_time = time.time() - groq_start
        
        if isinstance(groq_response, dict) and 'text' in groq_response:
            print(f"✅ Groq: {groq_response['text'][:150]}... ({groq_time:.2f}s)")
            groq_success = True
        else:
            print(f"❌ Groq failed")
            groq_success = False
    except Exception as e:
        print(f"❌ Groq error: {e}")
        groq_success = False
    
    return or_success and groq_success

async def main():
    """Main test runner"""
    print("🌐 OpenRouter Kimi Model Test Suite")
    print("=" * 60)
    print(f"Testing model: {OPENROUTER_MODEL}")
    print(f"API endpoint: https://openrouter.ai/api/v1")
    
    results = []
    
    # Test basic functionality
    basic_success = await test_openrouter_kimi_basic()
    results.append(("Basic", basic_success))
    
    # Test streaming if basic works
    streaming_success = False
    if basic_success:
        streaming_success = await test_openrouter_kimi_streaming()
        results.append(("Streaming", streaming_success))
    
    # Test complex query if basic works
    complex_success = False
    if basic_success:
        complex_success = await test_openrouter_kimi_complex()
        results.append(("Complex", complex_success))
    
    # Test comparison if basic works
    comparison_success = False
    if basic_success:
        comparison_success = await test_openrouter_comparison()
        results.append(("Comparison", comparison_success))
    
    # Summary
    print(f"\n📊 OpenRouter Test Results")
    print("=" * 35)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nOverall: {successful_tests}/{total_tests} tests passed")
    
    if basic_success:
        print("\n🎉 OpenRouter Kimi model is working!")
        if streaming_success and complex_success:
            print("🌟 All functionality tests passed - ready for production use!")
            if comparison_success:
                print("⚡ Both OpenRouter and Groq are working - you have options!")
        elif streaming_success:
            print("✅ Basic and streaming work - complex queries may have issues")
        else:
            print("⚠️  Basic functionality works but streaming may have issues")
    else:
        print("\n❌ OpenRouter Kimi model has configuration or connectivity issues")
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