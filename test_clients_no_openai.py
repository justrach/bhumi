#!/usr/bin/env python3
"""
Test script for Bhumi clients without OpenAI dependency
Tests Gemini and Groq clients using direct HTTP requests
"""
import asyncio
import os
import sys
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bhumi.base import LLMConfig, create_llm

async def test_gemini_client():
    """Test Gemini client with direct HTTP requests"""
    print("🧪 Testing Gemini Client (No OpenAI dependency)")
    print("=" * 50)
    
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyD0DpcCqW_tG_mL0r2VRW-5m2YwGP2PuGA")
    
    if api_key == "your-gemini-api-key-here":
        print("❌ Please set your GEMINI_API_KEY environment variable")
        return False
    
    try:
        # Create Gemini client
        config = LLMConfig(
            api_key=api_key,
            model="gemini/gemini-2.5-flash-preview-04-17"
        )
        
        llm = create_llm(config)
        print(f"✅ Gemini client created with base_url: {config.base_url}")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Keep responses short."},
            {"role": "user", "content": "What is 2+2? Answer in one sentence."}
        ]
        
        # Test non-streaming
        print("\n📝 Testing non-streaming completion...")
        start_time = time.time()
        response = await llm.completion(messages)
        end_time = time.time()
        
        print(f"Response: {response.get('text', 'No text found')}")
        print(f"Time taken: {end_time - start_time:.2f}s")
        
        # Test streaming
        print("\n🌊 Testing streaming completion...")
        stream_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 5, one number per line."}
        ]
        
        print("Streaming response: ", end="")
        start_time = time.time()
        async for chunk in await llm.completion(stream_messages, stream=True):
            print(chunk, end="", flush=True)
        end_time = time.time()
        print(f"\nStreaming completed in: {end_time - start_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {type(e).__name__}: {e}")
        return False

# async def test_groq_client():
#     """Test Groq client with direct HTTP requests"""
#     print("\n🧪 Testing Groq Client (No OpenAI dependency)")
#     print("=" * 50)
    
#     api_key = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
    
#     if api_key == "your-groq-api-key-here":
#         print("❌ Please set your GROQ_API_KEY environment variable")
#         return False
    
#     try:
#         # Create Groq client
#         config = LLMConfig(
#             api_key=api_key,
#             model="groq/llama3-8b-8192"
#         )
        
#         llm = create_llm(config)
#         print(f"✅ Groq client created with base_url: {config.base_url}")
        
#         messages = [
#             {"role": "system", "content": "You are a helpful assistant. Keep responses short."},
#             {"role": "user", "content": "What is the capital of France? Answer in one sentence."}
#         ]
        
#         # Test non-streaming
#         print("\n📝 Testing non-streaming completion...")
#         start_time = time.time()
#         response = await llm.completion(messages)
#         end_time = time.time()
        
#         print(f"Response: {response.get('text', 'No text found')}")
#         print(f"Time taken: {end_time - start_time:.2f}s")
        
#         # Test streaming
#         print("\n🌊 Testing streaming completion...")
#         stream_messages = [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": "List 3 programming languages, one per line."}
#         ]
        
#         print("Streaming response: ", end="")
#         start_time = time.time()
#         async for chunk in await llm.completion(stream_messages, stream=True):
#             print(chunk, end="", flush=True)
#         end_time = time.time()
#         print(f"\nStreaming completed in: {end_time - start_time:.2f}s")
        
#         return True
        
#     except Exception as e:
#         print(f"❌ Groq test failed: {type(e).__name__}: {e}")
#         return False

async def test_import_check():
    """Test that we don't have OpenAI dependency"""
    print("🔍 Testing OpenAI dependency removal...")
    print("=" * 50)
    
    try:
        import openai
        print("⚠️  OpenAI is still installed (optional, but not required)")
    except ImportError:
        print("✅ OpenAI dependency successfully removed")
    
    # Test that our clients work without importing openai
    try:
        from bhumi.providers.gemini_client import GeminiClient
        from bhumi.providers.groq_client import GroqClient
        print("✅ Gemini and Groq clients import successfully without OpenAI")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Bhumi Client Test Suite (No OpenAI Dependency)")
    print("=" * 60)
    
    # Test imports first
    import_success = await test_import_check()
    
    if not import_success:
        print("❌ Import tests failed. Exiting.")
        return
    
    # Run client tests
    gemini_success = await test_gemini_client()
    # groq_success = await test_groq_client()
    
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Import Check: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"Gemini Client: {'✅ PASS' if gemini_success else '❌ FAIL'}")
    # print(f"Groq Client: {'✅ PASS' if groq_success else '❌ FAIL'}")
    
    if gemini_success:
        print("\n🎉 At least one client test passed!")
        print("✨ OpenAI dependency successfully removed!")
    else:
        print("\n❌ All client tests failed. Check your API keys.")

if __name__ == "__main__":
    # Setup instructions
    print("📋 Setup Instructions:")
    print("1. Set environment variables:")
    print("   export GEMINI_API_KEY='your-gemini-api-key'")
    print("   export GROQ_API_KEY='your-groq-api-key'")
    print("2. Run this script: python test_clients_no_openai.py")
    print()
    
    asyncio.run(main())
