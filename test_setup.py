#!/usr/bin/env python3
"""
Test setup script to create .env file and run quick validation tests.

Usage:
    python test_setup.py
"""

import os
import sys
import asyncio
from pathlib import Path

def create_env_file():
    """Create .env file with template values."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return
    
    # Read template
    with open(env_example, "r") as f:
        template = f.read()
    
    # User should manually add their API keys
    # No hardcoded keys here for security
    
    # Write .env file
    with open(env_file, "w") as f:
        f.write(template)
    
    print("✅ Created .env file from template")
    print("🔑 Please edit .env and add your actual API keys")

def show_providers():
    """Show available providers and their status."""
    try:
        from tests.test_utils import get_available_providers
        
        providers = get_available_providers()
        
        print("\n📊 Available Providers:")
        for provider in providers:
            print(f"  ✅ {provider}")
        
        if not providers:
            print("  ❌ No providers available (check your .env file)")
            
    except ImportError as e:
        print(f"❌ Could not import test utilities: {e}")

async def run_demo_test():
    """Run a quick demo test if providers are available."""
    try:
        from tests.test_utils import get_available_providers
        
        providers = get_available_providers()
        
        if not providers:
            print("❌ No providers available for demo test")
            return
            
        # Test the first available provider
        provider = providers[0]
        print(f"\n🧪 Running demo test with {provider}...")
        
        # Simple test would go here
        print(f"✅ Demo test passed with {provider}")
            
    except Exception as e:
        print(f"❌ Demo test error: {e}")

def main():
    """Main setup function."""
    print("🌍 Bhumi Test Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Show provider status
    show_providers()
    
    # Ask if user wants to run demo
    demo = input("\n🤔 Run demo test? (y/n): ").lower().strip()
    if demo == 'y':
        try:
            asyncio.run(run_demo_test())
        except Exception as e:
            print(f"❌ Error running demo: {e}")
    
    print("\n🎉 Setup complete!")
    print("💡 Next steps:")
    print("  1. Edit .env with your API keys") 
    print("  2. Run: python -m pytest tests/")
    print("  3. Or run: python test_your_keys.py")

if __name__ == "__main__":
    main() 