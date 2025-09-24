"""
OpenAI GPT-5 vs Anthropic Claude Sonnet 4: Structured Outputs Comparison

This script compares both providers using their optimal approaches:
- OpenAI GPT-5: New Responses API with native structured outputs
- Anthropic Claude Sonnet 4: Prompt engineering with JSON generation

Both use high-performance Satya validation for 2-7x speedup over Pydantic.
"""

import asyncio
import os
import json
import time
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

# Import Satya for high-performance validation
from satya import Model, Field
from typing import List, Optional

# Load environment variables
load_dotenv()

# Shared Satya models for both providers
class Address(Model):
    """User address with validation"""
    street: str = Field(description="Street address", min_length=1, max_length=200)
    city: str = Field(description="City name", min_length=1, max_length=100)
    state: str = Field(description="State or province", min_length=1, max_length=100)
    country: str = Field(description="Country name", min_length=1, max_length=100)
    postal_code: str = Field(description="Postal/ZIP code", min_length=3, max_length=20)

class SimpleUser(Model):
    """Simple user model for testing"""
    user_id: str = Field(description="User ID", min_length=3, max_length=50)
    username: str = Field(description="Username", min_length=3, max_length=50)
    email: str = Field(description="Email address", email=True)
    full_name: str = Field(description="Full name", min_length=1, max_length=200)
    age: int = Field(description="Age", ge=1, le=150)

class ComplexUser(Model):
    """Complex user model with nested data"""
    user_id: str = Field(description="User ID", min_length=3, max_length=50)
    username: str = Field(description="Username", min_length=3, max_length=50)
    email: str = Field(description="Email address", email=True)
    full_name: str = Field(description="Full name", min_length=1, max_length=200)
    age: int = Field(description="Age", ge=1, le=150)
    address: Address = Field(description="User's address")
    tags: List[str] = Field(description="User tags", max_items=10, default=[])
    is_active: bool = Field(description="Account status", default=True)

class WeatherQuery(Model):
    """Weather query parameters"""
    location: str = Field(description="Location for weather query", min_length=2, max_length=100)
    units: str = Field(description="Temperature units (celsius or fahrenheit)", default="celsius")
    include_forecast: bool = Field(description="Include forecast data", default=False)
    days: int = Field(description="Number of forecast days", ge=1, le=14, default=1)

async def test_openai_gpt5(test_case):
    """Test OpenAI GPT-5 with new Responses API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "No OPENAI_API_KEY found"}
    
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config)
    
    start_time = time.time()
    
    try:
        # Use new Responses API pattern with separated instructions
        completion = await client.parse(
            instructions=f"You are a helpful assistant that generates structured data using the {test_case['model'].__name__} schema. Always respond with valid JSON that matches the schema exactly.",
            input=test_case["prompt"],
            text_format=test_case["model"],
            timeout=30.0
        )
        
        end_time = time.time()
        
        if completion.choices and len(completion.choices) > 0:
            result = completion.parsed
            if result:
                return {
                    "success": True,
                    "provider": "OpenAI GPT-5",
                    "api_type": "Responses API (separated instructions)",
                    "model": completion.model,
                    "response_time": round(end_time - start_time, 2),
                    "parsed_data": result,
                    "validation": "Satya ✅"
                }
        
        return {"error": "No parsed data from OpenAI"}
        
    except Exception as e:
        return {"error": f"OpenAI error: {e}"}

async def test_anthropic_claude(test_case):
    """Test Anthropic Claude Sonnet 4 with prompt engineering"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "No ANTHROPIC_API_KEY found"}
    
    config = LLMConfig(
        api_key=api_key,
        model="anthropic/claude-sonnet-4-20250514",
        debug=False
    )
    client = BaseLLMClient(config)
    
    start_time = time.time()
    
    try:
        # Create schema description for prompt engineering
        schema_description = f"""Create a {test_case['model'].__name__} in JSON format with these exact fields:
"""
        
        # Get schema fields dynamically
        if hasattr(test_case['model'], '__fields__'):
            for field_name, field in test_case['model'].__fields__.items():
                field_type = getattr(field, 'type_', 'string')
                if hasattr(field_type, '__name__'):
                    type_name = field_type.__name__
                else:
                    type_name = str(field_type)
                schema_description += f"- {field_name} ({type_name}): {getattr(field, 'description', 'field value')}\n"
        
        schema_description += f"\nUser request: {test_case['prompt']}\n\nRespond with ONLY valid JSON, no explanations or markdown:"
        
        response = await client.completion([{
            "role": "user",
            "content": schema_description
        }], timeout=30)
        
        end_time = time.time()
        
        # Extract text from Anthropic response
        if isinstance(response, dict) and 'raw_response' in response:
            content = response['raw_response']['content']
            if isinstance(content, list) and len(content) > 0:
                response_text = content[0].get('text', '')
            else:
                response_text = str(response)
        else:
            response_text = str(response)
        
        # Clean and parse JSON
        json_text = response_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        # Parse and validate with Satya
        parsed_json = json.loads(json_text)
        result = test_case['model'](**parsed_json)
        
        return {
            "success": True,
            "provider": "Anthropic Claude Sonnet 4",
            "api_type": "Chat Completions (prompt engineering)",
            "model": "claude-sonnet-4-20250514",
            "response_time": round(end_time - start_time, 2),
            "parsed_data": result,
            "validation": "Satya ✅"
        }
        
    except json.JSONDecodeError as e:
        return {"error": f"Anthropic JSON parsing failed: {e}"}
    except Exception as e:
        return {"error": f"Anthropic error: {e}"}

async def run_comparison():
    """Run comprehensive comparison between OpenAI and Anthropic"""
    print("=" * 80)
    print("🚀 OpenAI GPT-5 vs Anthropic Claude Sonnet 4: Structured Outputs Comparison")
    print("=" * 80)
    print("📊 Testing both providers with identical Satya models and prompts")
    print("🔥 OpenAI: New Responses API with native structured outputs")
    print("🧠 Anthropic: Prompt engineering with JSON generation")
    print("⚡ Both: High-performance Satya validation (2-7x faster than Pydantic)")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple User Profile",
            "model": SimpleUser,
            "prompt": "Create a user profile for John Smith, 30 years old, email john@example.com, username johnsmith"
        },
        {
            "name": "Complex User with Address",
            "model": ComplexUser,
            "prompt": "Create a user profile for Sarah Johnson, 28, from London UK, email sarah@example.com, username sarahj, tags: premium, verified"
        },
        {
            "name": "Weather Query",
            "model": WeatherQuery,
            "prompt": "Get weather for Tokyo with 3-day forecast in fahrenheit"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 60)
        
        # Test both providers concurrently
        openai_task = test_openai_gpt5(test_case)
        anthropic_task = test_anthropic_claude(test_case)
        
        openai_result, anthropic_result = await asyncio.gather(openai_task, anthropic_task)
        
        # Display results
        print(f"📊 Results for {test_case['name']}:")
        print()
        
        # OpenAI Results
        if openai_result.get("success"):
            print("✅ OpenAI GPT-5:")
            print(f"   🔗 API: {openai_result['api_type']}")
            print(f"   🕐 Time: {openai_result['response_time']}s")
            print(f"   🤖 Model: {openai_result['model']}")
            print(f"   ✅ Validation: {openai_result['validation']}")
            
            # Display parsed data
            data = openai_result['parsed_data']
            if hasattr(data, 'full_name'):
                print(f"   👤 Data: {data.full_name}, {data.age}, {data.email}")
            elif hasattr(data, 'location'):
                print(f"   🌤️  Data: {data.location}, {data.units}, {data.days} days")
        else:
            print(f"❌ OpenAI GPT-5: {openai_result.get('error', 'Unknown error')}")
        
        print()
        
        # Anthropic Results
        if anthropic_result.get("success"):
            print("✅ Anthropic Claude Sonnet 4:")
            print(f"   🔗 API: {anthropic_result['api_type']}")
            print(f"   🕐 Time: {anthropic_result['response_time']}s")
            print(f"   🤖 Model: {anthropic_result['model']}")
            print(f"   ✅ Validation: {anthropic_result['validation']}")
            
            # Display parsed data
            data = anthropic_result['parsed_data']
            if hasattr(data, 'full_name'):
                print(f"   👤 Data: {data.full_name}, {data.age}, {data.email}")
            elif hasattr(data, 'location'):
                print(f"   🌤️  Data: {data.location}, {data.units}, {data.days} days")
        else:
            print(f"❌ Anthropic Claude Sonnet 4: {anthropic_result.get('error', 'Unknown error')}")
        
        # Store results for summary
        results.append({
            "test": test_case['name'],
            "openai": openai_result,
            "anthropic": anthropic_result
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 COMPARISON SUMMARY")
    print("=" * 80)
    
    openai_successes = sum(1 for r in results if r['openai'].get('success'))
    anthropic_successes = sum(1 for r in results if r['anthropic'].get('success'))
    
    openai_avg_time = sum(r['openai'].get('response_time', 0) for r in results if r['openai'].get('success')) / max(openai_successes, 1)
    anthropic_avg_time = sum(r['anthropic'].get('response_time', 0) for r in results if r['anthropic'].get('success')) / max(anthropic_successes, 1)
    
    print(f"🏆 Success Rate:")
    print(f"   OpenAI GPT-5: {openai_successes}/{len(test_cases)} ({openai_successes/len(test_cases)*100:.0f}%)")
    print(f"   Anthropic Claude Sonnet 4: {anthropic_successes}/{len(test_cases)} ({anthropic_successes/len(test_cases)*100:.0f}%)")
    print()
    print(f"⚡ Average Response Time:")
    print(f"   OpenAI GPT-5: {openai_avg_time:.2f}s")
    print(f"   Anthropic Claude Sonnet 4: {anthropic_avg_time:.2f}s")
    print()
    print(f"🔧 Technical Approach:")
    print(f"   OpenAI: Native Responses API with structured outputs")
    print(f"   Anthropic: Prompt engineering with JSON generation")
    print()
    print(f"⚡ Performance:")
    print(f"   Both: Satya validation provides 2-7x speedup over Pydantic")
    print(f"   Both: Production-ready with comprehensive error handling")
    print()
    
    # Winner determination
    if openai_successes > anthropic_successes:
        print("🥇 Winner: OpenAI GPT-5 (higher success rate)")
    elif anthropic_successes > openai_successes:
        print("🥇 Winner: Anthropic Claude Sonnet 4 (higher success rate)")
    elif openai_avg_time < anthropic_avg_time:
        print("🥇 Winner: OpenAI GPT-5 (faster response time)")
    elif anthropic_avg_time < openai_avg_time:
        print("🥇 Winner: Anthropic Claude Sonnet 4 (faster response time)")
    else:
        print("🤝 Result: Tie - Both providers perform excellently!")
    
    print("\n💡 Recommendations:")
    print("   • OpenAI: Best for native structured outputs and new Responses API features")
    print("   • Anthropic: Excellent for complex reasoning and prompt engineering")
    print("   • Both: Use Satya for high-performance validation in production")
    print("   • Bhumi: Provides unified interface with provider-specific optimizations")

if __name__ == "__main__":
    asyncio.run(run_comparison())
