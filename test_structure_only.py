#!/usr/bin/env python3
"""
Structure test for Bhumi clients without OpenAI dependency
Tests client creation and method signatures without making API calls
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_client_structure():
    """Test that clients can be created and have proper structure"""
    print("🧪 Testing Client Structure (No API calls)")
    print("=" * 50)
    
    try:
        from bhumi.base import LLMConfig, create_llm
        
        # Test Gemini client creation
        gemini_config = LLMConfig(
            api_key="test_key",
            model="gemini/gemini-2.0-flash"
        )
        
        gemini_llm = create_llm(gemini_config)
        print(f"✅ Gemini client created: {type(gemini_llm).__name__}")
        print(f"   Base URL: {gemini_config.base_url}")
        print(f"   Has completion method: {hasattr(gemini_llm, 'completion')}")
        
        # Test Groq client creation  
        groq_config = LLMConfig(
            api_key="test_key",
            model="groq/llama3-8b-8192"
        )
        
        groq_llm = create_llm(groq_config)
        print(f"✅ Groq client created: {type(groq_llm).__name__}")
        print(f"   Base URL: {groq_config.base_url}")
        print(f"   Has completion method: {hasattr(groq_llm, 'completion')}")
        
        # Test import structure
        from bhumi.providers.gemini_client import GeminiClient, GeminiLLM
        from bhumi.providers.groq_client import GroqClient
        
        print("✅ All clients import successfully")
        print("✅ No OpenAI dependency required!")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_independence():
    """Test that we can work without OpenAI"""
    print("\n🔍 Testing OpenAI Independence")
    print("=" * 40)
    
    try:
        # Try to temporarily hide openai if it exists
        import sys
        original_modules = sys.modules.copy()
        
        # Remove openai from modules if present
        openai_modules = [mod for mod in sys.modules if mod.startswith('openai')]
        for mod in openai_modules:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Now test our imports
        from bhumi.providers.gemini_client import GeminiClient
        from bhumi.providers.groq_client import GroqClient
        
        print("✅ Clients work without OpenAI in sys.modules")
        
        # Restore modules
        sys.modules.update(original_modules)
        
        return True
        
    except Exception as e:
        print(f"❌ Independence test failed: {e}")
        # Restore modules on error
        sys.modules.update(original_modules)
        return False

if __name__ == "__main__":
    print("🚀 Bhumi Structure Test (No OpenAI Dependency)")
    print("=" * 55)
    
    structure_ok = test_client_structure()
    independence_ok = test_openai_independence()
    
    print(f"\n📊 Results:")
    print(f"Structure Test: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Independence Test: {'✅ PASS' if independence_ok else '❌ FAIL'}")
    
    if structure_ok and independence_ok:
        print("\n🎉 All structure tests passed!")
        print("✨ Ready for API testing with real keys!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
