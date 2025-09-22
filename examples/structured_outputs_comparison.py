"""
Comparison: Old vs New Structured Outputs Implementation

This example demonstrates the differences between the old bhumi structured outputs
and the new implementation that follows OpenAI/Anthropic patterns.
"""

import asyncio
import os
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from bhumi.base_client import BaseLLMClient, LLMConfig
from bhumi.structured_outputs import ResponseFormat, pydantic_function_tool


# Shared data model
class UserProfile(BaseModel):
    """Complete user profile information"""
    user_id: str = Field(pattern="^usr_[a-zA-Z0-9]+$", description="Unique user ID")
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: str = Field(description="Email address")
    full_name: str = Field(min_length=1, description="Full name")
    age: int = Field(ge=13, le=120, description="User age")


async def demo_old_approach():
    """Demonstrate the old structured outputs approach"""
    print("=" * 60)
    print("OLD APPROACH (Deprecated)")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=False
    )
    
    client = BaseLLMClient(config)
    
    # Old way: Use set_structured_output (now deprecated)
    print("🔧 Using set_structured_output() method (deprecated)...")
    client.set_structured_output(UserProfile)
    
    try:
        response = await client.completion([
            {"role": "system", "content": "Generate a realistic user profile. Use the generate_structured_output tool."},
            {"role": "user", "content": "Create a user profile for Alice from Seattle"}
        ])
        
        print("✅ Old approach completed:")
        print(f"   Response type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Content length: {len(response.get('text', ''))}")
            print(f"   First 100 chars: {response.get('text', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ Old approach failed: {e}")


async def demo_new_approach():
    """Demonstrate the new structured outputs approach"""
    print("\n" + "=" * 60)
    print("NEW APPROACH (Recommended)")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=False
    )
    
    client = BaseLLMClient(config)
    
    # New way: Use parse() method directly (similar to OpenAI)
    print("🚀 Using parse() method (OpenAI-style)...")
    
    try:
        completion = await client.parse(
            messages=[
                {"role": "system", "content": "Generate a realistic user profile matching the provided schema."},
                {"role": "user", "content": "Create a user profile for Alice from Seattle"}
            ],
            response_format=UserProfile  # Pass Pydantic model directly
        )
        
        print("✅ New approach completed:")
        print(f"   Response type: {type(completion)}")
        print(f"   Completion ID: {completion.id}")
        print(f"   Model: {completion.model}")
        
        # Access parsed data directly
        user = completion.parsed
        if user:
            print("✅ Structured data parsed successfully:")
            print(f"   User ID: {user.user_id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Age: {user.age}")
        else:
            print("❌ No structured data parsed")
            if completion.choices[0].message.refusal:
                print(f"   Refusal: {completion.choices[0].message.refusal}")
    
    except Exception as e:
        print(f"❌ New approach failed: {e}")


def demo_response_format_creation():
    """Show different ways to create response formats"""
    print("\n" + "=" * 60)
    print("RESPONSE FORMAT CREATION")
    print("=" * 60)
    
    # Method 1: From Pydantic model (recommended)
    print("🔧 Method 1: ResponseFormat.from_model()")
    format1 = ResponseFormat.from_model(UserProfile, name="user_profile")
    print(f"   Type: {format1['type']}")
    print(f"   Schema name: {format1['json_schema']['name']}")
    print(f"   Strict mode: {format1['json_schema']['strict']}")
    
    # Method 2: JSON object mode
    print("\n🔧 Method 2: ResponseFormat.json_object()")
    format2 = ResponseFormat.json_object()
    print(f"   Type: {format2['type']}")
    
    # Method 3: Custom JSON schema
    print("\n🔧 Method 3: ResponseFormat.json_schema()")
    custom_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["name", "value"]
    }
    format3 = ResponseFormat.json_schema(custom_schema, name="custom")
    print(f"   Type: {format3['type']}")
    print(f"   Schema name: {format3['json_schema']['name']}")


def demo_tool_creation():
    """Show different ways to create tools"""
    print("\n" + "=" * 60)
    print("TOOL CREATION")
    print("=" * 60)
    
    # OpenAI-style function tool
    print("🔧 OpenAI-style function tool:")
    openai_tool = pydantic_function_tool(UserProfile, name="create_user", description="Create a new user profile")
    print(f"   Type: {openai_tool['type']}")
    print(f"   Function name: {openai_tool['function']['name']}")
    print(f"   Strict mode: {openai_tool['function']['strict']}")
    
    # Anthropic-style tool schema
    print("\n🔧 Anthropic-style tool schema:")
    from bhumi.structured_outputs import pydantic_tool_schema
    anthropic_tool = pydantic_tool_schema(UserProfile)
    print(f"   Name: {anthropic_tool['name']}")
    print(f"   Has input_schema: {'input_schema' in anthropic_tool}")


async def demo_key_advantages():
    """Highlight key advantages of the new approach"""
    print("\n" + "=" * 60)
    print("KEY ADVANTAGES OF NEW APPROACH")
    print("=" * 60)
    
    print("✅ ADVANTAGES:")
    print("   1. 🎯 OpenAI/Anthropic API compatibility")
    print("   2. 🚀 Direct model parsing with client.parse()")
    print("   3. 🛡️  Built-in error handling (length, content filter, refusal)")
    print("   4. 📊 Structured response objects (ParsedChatCompletion)")
    print("   5. 🔧 Multiple response format options")
    print("   6. 🛠️  Tool creation helpers for both OpenAI and Anthropic")
    print("   7. ✨ Automatic JSON schema generation")
    print("   8. 🧪 Comprehensive test coverage")
    
    print("\n❌ OLD APPROACH LIMITATIONS:")
    print("   1. 🔗 Required tool registration step")
    print("   2. 🐌 Less direct API usage pattern")  
    print("   3. 🚫 No built-in error handling for edge cases")
    print("   4. 📝 Manual response parsing required")
    print("   5. 🔧 Limited response format options")


async def main():
    """Run comparison demo"""
    print("🔄 Bhumi Structured Outputs: Old vs New")
    print("Following OpenAI and Anthropic industry patterns\n")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OPENAI_API_KEY found - running format/tool demos only")
        demo_response_format_creation()
        demo_tool_creation()
        await demo_key_advantages()
        return
    
    # Run full comparison with API calls
    await demo_old_approach()
    await demo_new_approach()
    demo_response_format_creation()
    demo_tool_creation()
    await demo_key_advantages()
    
    print("\n" + "=" * 60)
    print("🎉 RECOMMENDATION: Use the new parse() method!")
    print("   It follows industry standards and provides better UX.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main())
