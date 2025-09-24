"""
Simple OpenAI vs Anthropic Comparison

Quick test to compare both providers with structured outputs.
"""

import asyncio
import os
import json
import time
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig
from satya import Model, Field

load_dotenv()

class SimpleUser(Model):
    """Simple user model for testing"""
    user_id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email address", email=True)
    full_name: str = Field(description="Full name")
    age: int = Field(description="Age", ge=1, le=150)

async def test_openai():
    """Test OpenAI GPT-5 with Responses API"""
    print("🔥 Testing OpenAI GPT-5 with new Responses API...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    config = LLMConfig(api_key=api_key, model="openai/gpt-5-nano")
    client = BaseLLMClient(config)
    
    start_time = time.time()
    
    try:
        # Use new Responses API with separated instructions (optimal)
        completion = await client.parse(
            instructions="You are a helpful assistant that generates structured data. Always respond with valid JSON that matches the schema exactly.",
            input="Create a user profile for John Smith, 30 years old, email john@example.com, username johnsmith",
            text_format=SimpleUser
        )
        
        end_time = time.time()
        
        if completion.choices and completion.parsed:
            user = completion.parsed
            return {
                "provider": "OpenAI GPT-5",
                "api": "Responses API (separated instructions)",
                "time": round(end_time - start_time, 2),
                "model": completion.model,
                "data": {
                    "name": user.full_name,
                    "age": user.age,
                    "email": user.email,
                    "username": user.username,
                    "id": user.user_id
                }
            }
        else:
            return {"error": "No parsed data from OpenAI"}
            
    except Exception as e:
        return {"error": f"OpenAI error: {e}"}

async def test_anthropic():
    """Test Anthropic Claude with prompt engineering"""
    print("🧠 Testing Anthropic Claude Sonnet 4 with prompt engineering...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found")
        return None
    
    config = LLMConfig(api_key=api_key, model="anthropic/claude-sonnet-4-20250514")
    client = BaseLLMClient(config)
    
    start_time = time.time()
    
    try:
        prompt = """Create a user profile in JSON format with these exact fields:
- user_id (string): unique ID
- username (string): username
- email (string): valid email
- full_name (string): full name
- age (number): age in years

For: John Smith, 30 years old, email john@example.com, username johnsmith

Respond with ONLY valid JSON, no explanations:"""

        response = await client.completion([{"role": "user", "content": prompt}])
        
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
        
        # Parse and validate
        json_text = response_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        parsed_json = json.loads(json_text)
        user = SimpleUser(**parsed_json)
        
        return {
            "provider": "Anthropic Claude Sonnet 4",
            "api": "Chat Completions (prompt engineering)",
            "time": round(end_time - start_time, 2),
            "model": "claude-sonnet-4-20250514",
            "data": {
                "name": user.full_name,
                "age": user.age,
                "email": user.email,
                "username": user.username,
                "id": user.user_id
            }
        }
        
    except Exception as e:
        return {"error": f"Anthropic error: {e}"}

async def main():
    """Run comparison"""
    print("=" * 70)
    print("🚀 OpenAI GPT-5 vs Anthropic Claude Sonnet 4 Comparison")
    print("=" * 70)
    print("⚡ Both using high-performance Satya validation")
    print()
    
    # Test OpenAI first
    openai_result = await test_openai()
    print()
    
    # Test Anthropic second
    anthropic_result = await test_anthropic()
    print()
    
    # Results
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    if openai_result and "error" not in openai_result:
        print("✅ OpenAI GPT-5:")
        print(f"   🔗 API: {openai_result['api']}")
        print(f"   🕐 Time: {openai_result['time']}s")
        print(f"   🤖 Model: {openai_result['model']}")
        print(f"   👤 Data: {openai_result['data']['name']}, {openai_result['data']['age']}, {openai_result['data']['email']}")
    else:
        print(f"❌ OpenAI GPT-5: {openai_result.get('error', 'Failed') if openai_result else 'No API key'}")
    
    print()
    
    if anthropic_result and "error" not in anthropic_result:
        print("✅ Anthropic Claude Sonnet 4:")
        print(f"   🔗 API: {anthropic_result['api']}")
        print(f"   🕐 Time: {anthropic_result['time']}s")
        print(f"   🤖 Model: {anthropic_result['model']}")
        print(f"   👤 Data: {anthropic_result['data']['name']}, {anthropic_result['data']['age']}, {anthropic_result['data']['email']}")
    else:
        print(f"❌ Anthropic Claude Sonnet 4: {anthropic_result.get('error', 'Failed') if anthropic_result else 'No API key'}")
    
    print()
    print("💡 Summary:")
    print("   • OpenAI: Native structured outputs with new Responses API")
    print("   • Anthropic: Excellent JSON generation with prompt engineering")
    print("   • Both: High-performance Satya validation (2-7x faster than Pydantic)")
    print("   • Both: Production-ready structured outputs")

if __name__ == "__main__":
    asyncio.run(main())
