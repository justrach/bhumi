"""
Satya High-Performance Structured Outputs Example

This example demonstrates using Bhumi's structured outputs with Satya models
for maximum performance. Works with current Satya v0.3 API.
"""

import asyncio
import os
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import Bhumi components
from bhumi.base_client import BaseLLMClient, LLMConfig

# Import Satya for high-performance validation
from satya import Model, Field

# Load environment variables
load_dotenv()


# Simple Satya models that work with current constraints
class UserProfile(Model):
    """User profile with Satya validation"""
    name: str = Field(description="Full name")
    age: int = Field(description="User age", ge=13, le=120)
    email: str = Field(description="Email address", email=True)
    is_active: bool = Field(description="Account status", default=True)


class WeatherQuery(Model):
    """Weather query with Satya validation"""
    location: str = Field(description="Location to get weather for")
    units: str = Field(description="Temperature units", default="celsius")
    include_forecast: bool = Field(description="Include forecast data", default=False)


async def demo_satya_structured_outputs():
    """Demonstrate Satya structured outputs"""
    print("🚀 Satya High-Performance Structured Outputs Demo")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return

    print(f"✅ Found API key (length: {len(api_key)})")

    # Create client
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-4o-mini",
        debug=False
    )

    client = BaseLLMClient(config)
    print("✅ BaseLLMClient created successfully!")

    # Test cases
    test_cases = [
        {
            "name": "User Profile",
            "model": UserProfile,
            "prompt": "Create a user profile for John Smith, 30 years old, email john@example.com"
        },
        {
            "name": "Weather Query",
            "model": WeatherQuery,
            "prompt": "Get weather for Tokyo with forecast in celsius"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 40)

        try:
            # Use Satya model with parse() method
            completion = await client.parse(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that generates structured data. Respond with valid JSON that matches the {test_case['model'].__name__} schema."
                    },
                    {
                        "role": "user",
                        "content": test_case["prompt"]
                    }
                ],
                response_format=test_case["model"]
            )

            print("✅ Request successful!")
            print(f"   Model: {completion.model}")
            print(f"   Completion ID: {completion.id}")

            # Access parsed data with Satya's high-performance validation
            result = completion.parsed
            if result:
                print("✅ Satya validation successful!")
                print(f"   Parsed type: {type(result).__name__}")

                # Display key fields
                if isinstance(result, UserProfile):
                    print("   📊 User Profile:")
                    print(f"      Name: {result.name}")
                    print(f"      Age: {result.age}")
                    print(f"      Email: {result.email}")
                    print(f"      Active: {result.is_active}")

                elif isinstance(result, WeatherQuery):
                    print("   🌤️  Weather Query:")
                    print(f"      Location: {result.location}")
                    print(f"      Units: {result.units}")
                    print(f"      Forecast: {result.include_forecast}")

            else:
                print("❌ No parsed data")
                if completion.choices[0].message.refusal:
                    print(f"   🤖 Model refused: {completion.choices[0].message.refusal}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"   Error type: {type(e).__name__}")

    print("\n" + "=" * 60)
    print("🎉 Satya Integration Demo Complete!")
    print("=" * 60)


def demo_satya_features():
    """Show Satya features and constraints"""
    print("\n📋 Satya v0.3 Features (Production-Ready)")
    print("-" * 50)

    print("✅ Supported Types:")
    print("   • str, int, float, bool")
    print("   • List, Dict, Tuple") 
    print("   • UUID, Decimal, datetime")
    print("   • Optional fields, nested models")

    print("\n✅ Supported Constraints:")
    print("   • String: min_length, max_length, pattern, email, url")
    print("   • Numeric: ge, le, gt, lt")
    print("   • Collections: min_items, max_items")

    print("\n⚡ Performance Benefits:")
    print("   • 2-7x faster than Pydantic")
    print("   • Rust-powered validation core")
    print("   • Batch processing (set_batch_size=1000)")
    print("   • Stream processing for large datasets")
    print("   • Memory-efficient design")

    print("\n🔧 Recommended Usage:")
    validator = UserProfile.validator()
    validator.set_batch_size(1000)
    print("   • Use batch processing for production workloads")
    print("   • Configure validator.set_batch_size(1000)")
    print("   • Use stream processing for unlimited datasets")


async def main():
    """Run Satya demo"""
    print("🚀 Bhumi + Satya: High-Performance Structured Outputs")
    print("Using optimized Satya v0.3 models with industry-standard patterns\n")

    # Show Satya features
    demo_satya_features()

    # Run actual API tests
    await demo_satya_structured_outputs()

    print("\n💡 Key Takeaways:")
    print("   • Satya provides 2-7x performance improvement over Pydantic")
    print("   • Same clean API as OpenAI's client.chat.completions.parse()")
    print("   • Works seamlessly with all Bhumi providers")
    print("   • Production-ready with comprehensive validation")


if __name__ == "__main__":
    asyncio.run(main())
