"""
Simple Provider Test Suite - Production Ready

This test suite focuses on core functionality without complex dependencies.
Skips MAP-Elites and complex Satya validation to ensure reliability.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def test_provider_basic(provider_name: str, api_key_env: str, model: str):
    """Test basic functionality for a provider"""
    print(f"\n🧪 Testing {provider_name}")
    print("-" * 40)
    
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"❌ No {api_key_env} found")
        return {"basic": False, "streaming": False, "reason": "no_api_key"}
    
    try:
        config = LLMConfig(api_key=api_key, model=model, timeout=30, debug=False)
        client = BaseLLMClient(config, debug=False)
        
        results = {"basic": False, "streaming": False}
        
        # Test 1: Basic completion
        try:
            print("📝 Testing basic completion...")
            response = await asyncio.wait_for(
                client.completion([
                    {"role": "user", "content": f"Say 'Hello from {provider_name}!'"}
                ], max_tokens=20),
                timeout=30
            )
            
            if response and response.get('text'):
                print(f"✅ Basic: {response['text'][:50]}...")
                results["basic"] = True
            else:
                print("❌ Basic: No response text")
        except Exception as e:
            print(f"❌ Basic: {str(e)[:80]}")
        
        # Test 2: Streaming
        try:
            print("🌊 Testing streaming...")
            chunks = []
            chunk_count = 0
            
            async for chunk in client.astream_completion([
                {"role": "user", "content": "Count: 1, 2, 3"}
            ], max_tokens=15):
                chunks.append(chunk)
                chunk_count += 1
                if chunk_count >= 5:  # Limit chunks
                    break
            
            content = "".join(chunks)
            if content.strip():
                print(f"✅ Streaming: {content[:30]}... ({chunk_count} chunks)")
                results["streaming"] = True
            else:
                print("❌ Streaming: No content")
        except Exception as e:
            print(f"❌ Streaming: {str(e)[:80]}")
        
        return results
        
    except Exception as e:
        print(f"❌ Provider setup failed: {str(e)[:80]}")
        return {"basic": False, "streaming": False, "reason": "setup_failed"}

async def run_simple_tests():
    """Run simple tests for all providers"""
    print("🚀 SIMPLE PROVIDER TEST SUITE")
    print("=" * 60)
    print("Testing core functionality without complex dependencies")
    print()
    
    # Provider configurations
    providers = [
        ("OpenAI GPT-4o-mini", "OPENAI_API_KEY", "openai/gpt-4o-mini"),
        ("OpenAI GPT-3.5", "OPENAI_API_KEY", "openai/gpt-3.5-turbo"),
        ("Anthropic Claude", "ANTHROPIC_API_KEY", "anthropic/claude-3-5-sonnet-20241022"),
        ("Anthropic Haiku", "ANTHROPIC_API_KEY", "anthropic/claude-3-5-haiku-20241022"),
        ("Google Gemini 2.0", "GEMINI_API_KEY", "gemini/gemini-2.0-flash"),
        ("Google Gemini 1.5", "GEMINI_API_KEY", "gemini/gemini-1.5-pro"),
        ("Groq Llama", "GROQ_API_KEY", "groq/llama-3.1-8b-instant"),
        ("Mistral Large", "MISTRAL_API_KEY", "mistral/mistral-large-latest"),
    ]
    
    results = {}
    
    for name, key_env, model in providers:
        try:
            result = await test_provider_basic(name, key_env, model)
            results[name] = result
            
            # Rate limiting prevention
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            results[name] = {"basic": False, "streaming": False, "reason": "test_failed"}
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"{'Provider':<20} {'Basic':<8} {'Streaming':<10} {'Status'}")
    print("-" * 60)
    
    total_tests = 0
    successful_tests = 0
    working_providers = 0
    
    for name, result in results.items():
        basic = "✅" if result.get("basic") else "❌"
        streaming = "✅" if result.get("streaming") else "❌"
        
        # Determine status
        if result.get("reason") == "no_api_key":
            status = "🔑 No Key"
        elif result.get("basic") and result.get("streaming"):
            status = "🎉 Perfect"
            working_providers += 1
        elif result.get("basic") or result.get("streaming"):
            status = "⚠️ Partial"
            working_providers += 1
        else:
            status = "❌ Failed"
        
        print(f"{name:<20} {basic:<8} {streaming:<10} {status}")
        
        # Count tests (skip no-key cases)
        if result.get("reason") != "no_api_key":
            total_tests += 2  # basic + streaming
            if result.get("basic"):
                successful_tests += 1
            if result.get("streaming"):
                successful_tests += 1
    
    # Final stats
    success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Working Providers: {working_providers}/{len([r for r in results.values() if r.get('reason') != 'no_api_key'])}")
    print(f"   Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 EXCELLENT! Ready for production!")
    elif success_rate >= 50:
        print("👍 GOOD! Most functionality working!")
    else:
        print("⚠️ NEEDS WORK: Several issues present")
    
    # Show working providers
    working = [name for name, result in results.items() if result.get("basic") or result.get("streaming")]
    if working:
        print(f"\n✅ Working Providers:")
        for provider in working:
            basic_status = "✅" if results[provider].get("basic") else "❌"
            stream_status = "✅" if results[provider].get("streaming") else "❌"
            print(f"   • {provider}: Basic {basic_status} Streaming {stream_status}")
    
    print(f"\n✅ Simple test suite completed!")
    return success_rate >= 50  # Return True if majority working

if __name__ == "__main__":
    asyncio.run(run_simple_tests())
