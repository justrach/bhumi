"""
Example: New structured outputs implementation following OpenAI/Anthropic patterns.

This example demonstrates:
1. Using the new parse() method (similar to OpenAI's client.chat.completions.parse())
2. Automatic JSON schema generation from Pydantic models
3. Response validation and error handling
4. Tool calling with structured outputs
"""

import asyncio
import os
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from bhumi.base_client import BaseLLMClient, LLMConfig
from bhumi.structured_outputs import (
    ResponseFormat,
    pydantic_function_tool,
    LengthFinishReasonError,
    ContentFilterFinishReasonError,
    StructuredOutputError
)


# Define structured data models
class Address(BaseModel):
    """User address information"""
    street: str = Field(description="Street address")
    city: str = Field(description="City name") 
    state: str = Field(description="State or province")
    country: str = Field(description="Country name")
    postal_code: str = Field(description="Postal/ZIP code")


class Subscription(BaseModel):
    """User subscription details"""
    plan: Literal["free", "basic", "premium"] = Field(description="Subscription plan type")
    status: Literal["active", "expired", "cancelled"] = Field(description="Current subscription status")
    start_date: datetime = Field(description="When the subscription started")
    end_date: Optional[datetime] = Field(None, description="When the subscription ends/ended")


class UserProfile(BaseModel):
    """Complete user profile information"""
    user_id: str = Field(pattern="^usr_[a-zA-Z0-9]+$", description="Unique user ID")
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: str = Field(description="Email address")
    full_name: str = Field(min_length=1, description="Full name")
    age: int = Field(ge=13, le=120, description="User age")
    address: Address = Field(description="User's address")
    subscription: Subscription = Field(description="Subscription information")
    created_at: datetime = Field(description="Account creation timestamp")


class WeatherQuery(BaseModel):
    """Weather query parameters"""
    location: str = Field(description="Location to get weather for")
    units: Literal["celsius", "fahrenheit"] = Field(default="celsius", description="Temperature units")
    include_forecast: bool = Field(default=False, description="Include forecast data")


class AnalysisResult(BaseModel):
    """Analysis result with confidence score"""
    summary: str = Field(description="Brief summary of the analysis")
    key_points: List[str] = Field(description="List of key points from the analysis")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    recommendations: List[str] = Field(description="List of recommendations based on analysis")


async def demo_basic_structured_parsing():
    """Demonstrate basic structured output parsing"""
    print("=" * 60)
    print("Demo: Basic Structured Output Parsing")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    try:
        # Use the new parse() method - similar to OpenAI's client.chat.completions.parse()
        completion = await client.parse(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that generates realistic user profiles."
                },
                {
                    "role": "user",
                    "content": "Create a user profile for a premium subscriber from San Francisco"
                }
            ],
            response_format=UserProfile  # Pass Pydantic model directly
        )
        
        print(f"✅ Successfully parsed response!")
        print(f"ID: {completion.id}")
        print(f"Model: {completion.model}")
        
        # Access the parsed data
        user = completion.parsed
        if user:
            print(f"\n📊 Parsed User Profile:")
            print(f"  User ID: {user.user_id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Full Name: {user.full_name}")
            print(f"  Age: {user.age}")
            print(f"  Address: {user.address.street}, {user.address.city}, {user.address.state}")
            print(f"  Subscription: {user.subscription.plan} ({user.subscription.status})")
            print(f"  Created: {user.created_at}")
        else:
            print("❌ No parsed data available")
            if completion.choices[0].message.refusal:
                print(f"Refusal: {completion.choices[0].message.refusal}")
    
    except LengthFinishReasonError:
        print("❌ Response was cut off due to length limits")
    except ContentFilterFinishReasonError:
        print("❌ Response was filtered by content policy")
    except StructuredOutputError as e:
        print(f"❌ Structured output error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def demo_multiple_formats():
    """Demonstrate multiple response formats"""
    print("\n" + "=" * 60)
    print("Demo: Multiple Response Formats")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    test_cases = [
        (WeatherQuery, "Create a weather query for Tokyo with forecast"),
        (AnalysisResult, "Analyze the benefits of renewable energy"),
    ]
    
    for model_class, prompt in test_cases:
        print(f"\n🧪 Testing {model_class.__name__}...")
        
        try:
            completion = await client.parse(
                messages=[
                    {"role": "system", "content": f"Generate a {model_class.__name__} based on the user request."},
                    {"role": "user", "content": prompt}
                ],
                response_format=model_class
            )
            
            result = completion.parsed
            if result:
                print(f"✅ Successfully parsed {model_class.__name__}:")
                # Pretty print the model data
                import json
                print(json.dumps(result.model_dump(), indent=2, default=str))
            else:
                print(f"❌ Failed to parse {model_class.__name__}")
        
        except Exception as e:
            print(f"❌ Error with {model_class.__name__}: {e}")


async def demo_tool_calling_with_structured_outputs():
    """Demonstrate tool calling with structured outputs"""
    print("\n" + "=" * 60)
    print("Demo: Tool Calling with Structured Outputs")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    # Register a tool using the new pydantic_function_tool helper
    async def analyze_data(**kwargs) -> dict:
        """Analyze data and return structured results"""
        try:
            # Validate input with Pydantic
            analysis_request = AnalysisResult(**kwargs)
            return {
                "status": "success",
                "analysis": analysis_request.model_dump()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Register tool with structured schema
    tool_def = pydantic_function_tool(AnalysisResult, name="analyze_data", description="Analyze data and return structured results")
    
    client.register_tool(
        name="analyze_data",
        func=analyze_data,
        description=tool_def["function"]["description"],
        parameters=tool_def["function"]["parameters"]
    )
    
    try:
        response = await client.completion([
            {
                "role": "system",
                "content": "You are a data analyst. Use the analyze_data tool when asked to analyze something."
            },
            {
                "role": "user",
                "content": "Please analyze the impact of remote work on productivity"
            }
        ])
        
        print("✅ Tool calling completed:")
        print(response.get("text", str(response)))
    
    except Exception as e:
        print(f"❌ Tool calling error: {e}")


async def demo_response_format_creation():
    """Demonstrate different ways to create response formats"""
    print("\n" + "=" * 60)
    print("Demo: Response Format Creation")
    print("=" * 60)
    
    # Method 1: From Pydantic model (recommended)
    format1 = ResponseFormat.from_model(UserProfile, name="user_profile")
    print("✅ ResponseFormat.from_model():")
    print(f"  Type: {format1['type']}")
    print(f"  Name: {format1['json_schema']['name']}")
    print(f"  Strict: {format1['json_schema']['strict']}")
    
    # Method 2: JSON object mode
    format2 = ResponseFormat.json_object()
    print("\n✅ ResponseFormat.json_object():")
    print(f"  Type: {format2['type']}")
    
    # Method 3: Custom JSON schema
    custom_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "status": {"type": "string", "enum": ["success", "error"]}
        },
        "required": ["message", "status"]
    }
    format3 = ResponseFormat.json_schema(custom_schema, name="custom_response")
    print("\n✅ ResponseFormat.json_schema():")
    print(f"  Type: {format3['type']}")
    print(f"  Name: {format3['json_schema']['name']}")


async def demo_error_handling():
    """Demonstrate comprehensive error handling"""
    print("\n" + "=" * 60)
    print("Demo: Error Handling")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=False  # Reduce noise for error demo
    )
    
    client = BaseLLMClient(config)
    
    # Test 1: Try streaming with parse() (should fail)
    print("🧪 Testing streaming with parse() (should fail)...")
    try:
        await client.parse(
            messages=[{"role": "user", "content": "Hello"}],
            response_format=WeatherQuery,
            stream=True  # This should raise ValueError
        )
        print("❌ Expected ValueError not raised")
    except ValueError as e:
        print(f"✅ Correctly caught ValueError: {e}")
    
    # Test 2: Handle unparseable response gracefully
    print("\n🧪 Testing response that might not parse (graceful handling)...")
    try:
        completion = await client.parse(
            messages=[
                {"role": "system", "content": "Respond with a simple greeting, not JSON."},
                {"role": "user", "content": "Say hello"}
            ],
            response_format=WeatherQuery
        )
        
        if completion.parsed is None:
            print("✅ Gracefully handled unparseable response")
            print(f"   Raw content: {completion.choices[0].message.content}")
        else:
            print("❌ Unexpectedly parsed non-JSON response")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def main():
    """Run all demos"""
    print("🚀 Bhumi Structured Outputs Demo - New Implementation")
    print("Following OpenAI and Anthropic patterns")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    await demo_basic_structured_parsing()
    await demo_multiple_formats()
    await demo_tool_calling_with_structured_outputs()
    await demo_response_format_creation()
    await demo_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main())
