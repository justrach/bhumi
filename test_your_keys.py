#!/usr/bin/env python3
"""
Test your API keys after adding them to .env
"""

import asyncio
import sys
sys.path.append('tests')

async def test_your_keys():
    """Quick test of user's API keys"""
    
    from test_utils import TestEnvironment, run_comprehensive_test
    
    print("🔑 Testing Your API Keys")
    print("=" * 30)
    
    TestEnvironment.load_env_file()
    
    # Test each provider the user cares about
    providers_to_test = ['anthropic', 'groq', 'openrouter']
    
    for provider in providers_to_test:
        key = TestEnvironment.get_api_key(provider)
        
        # Check if key exists and isn't a placeholder
        placeholder_patterns = ['your-', 'your_', 'key-here', 'api-key-here']
        is_placeholder = any(pattern in (key or '') for pattern in placeholder_patterns)
        
        if not key or is_placeholder:
            print(f"🔒 {provider.upper()}: Add your key to .env")
            continue
            
        print(f"🧪 Testing {provider.upper()}...")
        try:
            results = await run_comprehensive_test(provider)
            passed = sum(1 for r in results if r.success)
            total = len(results)
            
            if passed == total:
                print(f"   ✅ {passed}/{total} tests passed!")
            else:
                print(f"   ⚠️ {passed}/{total} tests passed")
                
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:50]}...")
    
    print("\n🎉 Test complete! Add missing keys to .env and run again.")

if __name__ == "__main__":
    asyncio.run(test_your_keys()) 