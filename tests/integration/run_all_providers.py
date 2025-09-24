"""
Master Test Runner for All Providers

Run comprehensive tests for all supported providers individually or together.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass  # dotenv not available, use environment variables as-is

def run_provider_tests(provider: str, verbose: bool = True, stop_on_first_failure: bool = False, simple_mode: bool = False, no_tools: bool = False):
    """Run tests for a specific provider"""
    # For other providers, no special handling needed
    if no_tools and provider == "cerebras":
        test_file = f"test_{provider}_no_tools.py"
    elif simple_mode and provider == "cerebras":
        test_file = f"test_{provider}_simple.py"
    else:
        test_file = f"test_{provider}_comprehensive.py"
    
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    mode_desc = ""
    if no_tools and provider == "cerebras":
        mode_desc = " (no tools)"
    elif simple_mode and provider == "cerebras":
        mode_desc = " (simple mode)"
    
    print(f"\n🚀 Running {provider.upper()} tests{mode_desc}...")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", str(test_path)]
    
    if verbose:
        cmd.append("-v")
    
    if stop_on_first_failure:
        cmd.append("-x")
    
    # Add coverage if available
    try:
        import pytest_cov
        cmd.extend(["--cov=bhumi", "--cov-report=term-missing"])
    except ImportError:
        pass
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent, capture_output=False)
        success = result.returncode == 0
        
        if success:
            print(f"✅ {provider.upper()} tests PASSED")
        else:
            print(f"❌ {provider.upper()} tests FAILED")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running {provider} tests: {e}")
        return False

def check_api_keys():
    """Check which API keys are available"""
    providers = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "gemini": "GEMINI_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY"
    }
    
    available = []
    missing = []
    
    for provider, key in providers.items():
        if os.getenv(key):
            available.append(provider)
        else:
            missing.append(provider)
    
    print("🔑 API Key Status:")
    for provider in available:
        print(f"   ✅ {provider.upper()}: Available")
    
    for provider in missing:
        print(f"   ❌ {provider.upper()}: Missing")
    
    return available, missing

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive tests for LLM providers")
    parser.add_argument(
        "providers", 
        nargs="*", 
        choices=["openai", "anthropic", "gemini", "cerebras", "groq", "mistral", "all"],
        help="Providers to test (default: all available)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-x", "--stop-on-failure", action="store_true", help="Stop on first failure")
    parser.add_argument("--check-keys", action="store_true", help="Only check API keys")
    parser.add_argument("--simple", action="store_true", help="Use simple tests for problematic providers (e.g., Cerebras)")
    parser.add_argument("--no-tools", action="store_true", help="Skip tool calling tests entirely (recommended for Cerebras)")
    
    args = parser.parse_args()
    
    print("🧪 Bhumi Comprehensive Provider Tests")
    print("=" * 50)
    
    # Check API keys
    available_providers, missing_providers = check_api_keys()
    
    if args.check_keys:
        return
    
    if not available_providers:
        print("\n❌ No API keys found! Please set at least one API key:")
        print("   export OPENAI_API_KEY=your_key")
        print("   export ANTHROPIC_API_KEY=your_key")
        print("   export GEMINI_API_KEY=your_key")
        print("   export CEREBRAS_API_KEY=your_key")
        print("   export GROQ_API_KEY=your_key")
        return
    
    # Determine which providers to test
    if not args.providers or "all" in args.providers:
        providers_to_test = available_providers
    else:
        providers_to_test = [p for p in args.providers if p in available_providers]
        
        # Warn about missing keys
        for provider in args.providers:
            if provider not in available_providers and provider != "all":
                print(f"⚠️  Skipping {provider.upper()}: No API key found")
    
    if not providers_to_test:
        print("\n❌ No providers available to test!")
        return
    
    print(f"\n🎯 Testing providers: {', '.join(p.upper() for p in providers_to_test)}")
    
    # Run tests for each provider
    results = {}
    
    for provider in providers_to_test:
        success = run_provider_tests(
            provider, 
            verbose=args.verbose, 
            stop_on_first_failure=args.stop_on_failure,
            simple_mode=args.simple,
            no_tools=args.no_tools
        )
        results[provider] = success
        
        if not success and args.stop_on_failure:
            print(f"\n🛑 Stopping due to failure in {provider.upper()} tests")
            break
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = []
    failed = []
    
    for provider, success in results.items():
        if success:
            passed.append(provider)
            print(f"✅ {provider.upper()}: PASSED")
        else:
            failed.append(provider)
            print(f"❌ {provider.upper()}: FAILED")
    
    print(f"\n🎯 Results: {len(passed)} passed, {len(failed)} failed")
    
    if failed:
        print(f"\n❌ Failed providers: {', '.join(f.upper() for f in failed)}")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")

if __name__ == "__main__":
    main()
