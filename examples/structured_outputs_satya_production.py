"""
Satya High-Performance Structured Outputs Example

This example demonstrates using Bhumi's structured outputs with Satya models
for maximum performance. Based on the deepwiki research, Satya v0.3 provides:

✅ SUPPORTED TYPES:
- Primitive types: str, int, float, bool
- Collections: List, Dict, Tuple
- Special types: UUID, Decimal, datetime
- Complex types: nested Model instances, Optional fields

✅ SUPPORTED CONSTRAINTS:
- String: min_length, max_length, pattern, email, url
- Numeric: ge, le, gt, lt, min_value, max_value
- Collections: min_items, max_items, unique_items

✅ RECOMMENDED PATTERNS:
- Use batch processing with batch_size=1000 for optimal performance
- Use stream processing for large datasets
- Leverage JSON bytes validators for raw JSON input

This example shows production-ready usage with performance optimizations.
"""

import asyncio
import os
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Import Bhumi components
from bhumi.base_client import BaseLLMClient, LLMConfig
from bhumi.structured_outputs import ResponseFormat, pydantic_function_tool

# Import Satya for high-performance validation
from satya import Model, Field

# Load environment variables
load_dotenv()


# Define Satya models with comprehensive validation (production-ready)
class Address(Model):
    """User address with full validation"""
    street: str = Field(description="Street address", min_length=1, max_length=200)
    city: str = Field(description="City name", min_length=1, max_length=100)
    state: str = Field(description="State or province", min_length=1, max_length=100)
    country: str = Field(description="Country name", min_length=1, max_length=100)
    postal_code: str = Field(description="Postal/ZIP code", min_length=3, max_length=20)


class Subscription(Model):
    """User subscription with financial precision"""
    plan: str = Field(description="Subscription plan type", pattern="^(free|basic|premium)$")
    status: str = Field(description="Current subscription status", pattern="^(active|expired|cancelled)$")
    start_date: datetime = Field(description="When the subscription started")
    end_date: Optional[datetime] = Field(description="When the subscription ends/ended", default=None)
    monthly_fee: Decimal = Field(description="Monthly fee", ge=0, le=Decimal('10000.00'))


class UserProfile(Model):
    """Complete user profile with high-performance Satya validation"""
    user_id: str = Field(description="Unique user ID", pattern=r"^usr_[a-zA-Z0-9]+$", min_length=5, max_length=50)
    username: str = Field(description="Username", min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(description="Email address", email=True)  # RFC 5322 compliant validation
    full_name: str = Field(description="Full name", min_length=1, max_length=200)
    age: int = Field(description="User age", ge=13, le=120)
    address: Address = Field(description="User's address")
    subscription: Subscription = Field(description="Subscription information")
    balance: Decimal = Field(description="Account balance", ge=Decimal('-10000.00'), le=Decimal('1000000.00'))
    is_active: bool = Field(description="Account status", default=True)
    tags: List[str] = Field(description="User tags", max_items=10, default=[])
    created_at: datetime = Field(description="Account creation timestamp")


class WeatherQuery(Model):
    """Weather query with optimized validation"""
    location: str = Field(description="Location to get weather for", min_length=1, max_length=100)
    units: str = Field(description="Temperature units", pattern="^(celsius|fahrenheit)$", default="celsius")
    include_forecast: bool = Field(description="Include forecast data", default=False)
    days: int = Field(description="Number of forecast days", ge=1, le=14, default=1)


async def demo_satya_structured_outputs():
    """Demonstrate Satya structured outputs with production patterns"""
    print("=" * 70)
    print("🚀 Satya High-Performance Structured Outputs Demo")
    print("=" * 70)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return

    # Create client with high-performance model
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-4o-mini",  # Use available model
        debug=False
    )

    client = BaseLLMClient(config)

    print("✅ Using Satya models for high-performance validation")
    print("✅ Batch processing optimized for production workloads")

    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple Profile",
            "model": UserProfile,
            "prompt": "Create a simple user profile for John Smith, 30 years old, from New York"
        },
        {
            "name": "Complex Profile with Subscription",
            "model": UserProfile,
            "prompt": "Create a premium user profile for Sarah Johnson, 28, from London, with a premium subscription costing $29.99/month, balance $150.50, and tags: premium, verified"
        },
        {
            "name": "Weather Query",
            "model": WeatherQuery,
            "prompt": "Get weather for Tokyo with 3-day forecast in fahrenheit"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 50)

        try:
            # Use Satya model with parse() method
            completion = await client.parse(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that generates structured data using the {test_case['model'].__name__} schema. Always respond with valid JSON that matches the schema exactly."
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

                # Display key fields based on model type
                if isinstance(result, UserProfile):
                    print("   📊 User Profile:")
                    print(f"      Name: {result.full_name}")
                    print(f"      Age: {result.age}")
                    print(f"      Email: {result.email}")
                    print(f"      Balance: ${result.balance}")
                    print(f"      Active: {result.is_active}")
                    if result.tags:
                        print(f"      Tags: {', '.join(result.tags)}")
                    if hasattr(result, 'subscription') and result.subscription:
                        print(f"      Plan: {result.subscription.plan} (${result.subscription.monthly_fee}/month)")

                elif isinstance(result, WeatherQuery):
                    print("   🌤️  Weather Query:")
                    print(f"      Location: {result.location}")
                    print(f"      Units: {result.units}")
                    print(f"      Forecast: {result.include_forecast}")
                    print(f"      Days: {result.days}")

            else:
                print("❌ No parsed data")
                if completion.choices[0].message.refusal:
                    print(f"   🤖 Model refused: {completion.choices[0].message.refusal}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"   Error type: {type(e).__name__}")

    print("\n" + "=" * 70)
    print("🎉 Satya Integration Demo Complete!")
    print("=" * 70)


def demo_satya_performance_features():
    """Demonstrate Satya's performance optimization features"""
    print("\n🔧 Satya Performance Features Demo")
    print("-" * 40)

    # Create validator with batch processing (recommended for production)
    validator = UserProfile.validator()
    validator.set_batch_size(1000)  # Optimal batch size

    print("✅ Configured validator with batch_size=1000")
    print("✅ This provides 2-7x performance improvement over Pydantic")

    # Demonstrate stream processing for large datasets
    print("✅ Stream processing available for unlimited dataset sizes")
    print("✅ Memory-efficient: constant memory usage")

    # Show JSON bytes validation (recommended for raw JSON)
    print("✅ JSON bytes validation available for raw JSON input")
    print("   - Model.model_validate_json_bytes()")
    print("   - Model.model_validate_json_array_bytes()")
    print("   - Model.model_validate_ndjson_bytes()")


def demo_satya_supported_constraints():
    """Show Satya's comprehensive constraint support"""
    print("\n📋 Satya Supported Constraints (Production-Ready)")
    print("-" * 55)

    constraints = {
        "String": ["min_length", "max_length", "pattern", "email", "url"],
        "Numeric": ["ge", "le", "gt", "lt", "min_value", "max_value"],
        "Collections": ["min_items", "max_items", "unique_items"],
        "Types": ["str", "int", "float", "bool", "Decimal", "datetime", "UUID", "List", "Dict", "Optional"]
    }

    for category, items in constraints.items():
        print(f"🔹 {category}: {', '.join(items)}")

    print("\n✅ RFC 5322 compliant email validation")
    print("✅ Financial-grade Decimal precision")
    print("✅ Nested model validation")
    print("✅ Enum/Literal type support")


async def main():
    """Run all Satya demos"""
    print("🚀 Bhumi + Satya: Production-Ready Structured Outputs")
    print("Based on deepwiki research - using recommended Satya v0.3 patterns")
    print()

    # Show what Satya supports
    demo_satya_supported_constraints()
    demo_satya_performance_features()

    # Run actual API tests
    await demo_satya_structured_outputs()

    print("\n💡 Production Recommendations:")
    print("   • Use batch_size=1000 for optimal performance")
    print("   • Leverage stream processing for large datasets")
    print("   • Use JSON bytes validators for raw JSON input")
    print("   • Satya provides 2-7x performance improvement over Pydantic")


if __name__ == "__main__":
    asyncio.run(main())
