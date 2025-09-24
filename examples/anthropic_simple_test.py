"""
Simple Anthropic Claude Sonnet 4 Test with JSON Output

This is a minimal test to verify Anthropic integration works with JSON generation
and Satya validation, using prompt engineering instead of structured outputs.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

# Simple Satya model for testing
from satya import Model, Field

class SimpleUser(Model):
    """Simple user model for testing"""
    user_id: str = Field(description="User ID")
    username: str = Field(description="Username") 
    email: str = Field(description="Email address", email=True)
    full_name: str = Field(description="Full name")
    age: int = Field(description="Age", ge=1, le=150)

async def test_anthropic():
    """Test Anthropic Claude with JSON output and Satya validation"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found")
        return
    
    print("🤖 Testing Anthropic Claude Sonnet 4...")
    
    # Create client
    config = LLMConfig(
        api_key=api_key,
        model="anthropic/claude-sonnet-4-20250514"
    )
    client = BaseLLMClient(config)
    
    try:
        # Test with prompt engineering for JSON
        prompt = """Create a user profile in JSON format with these exact fields:
- user_id (string): unique ID
- username (string): username
- email (string): valid email
- full_name (string): full name  
- age (number): age in years

For: Sarah Johnson, 28 years old, email sarah@example.com

Respond with ONLY valid JSON, no explanations or markdown:"""

        response = await client.completion([{"role": "user", "content": prompt}])
        
        print("✅ Anthropic request successful!")
        
        # Extract response text properly from Anthropic format
        if isinstance(response, dict):
            if 'raw_response' in response and 'content' in response['raw_response']:
                # Extract from Anthropic response format
                content = response['raw_response']['content']
                if isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
                else:
                    response_text = str(response)
            elif 'text' in response:
                # Check if text field contains the actual response or a string representation
                text_field = response['text']
                if isinstance(text_field, str) and text_field.startswith('{') and 'content' in text_field:
                    # This is a string representation of the response dict, need to parse it
                    import ast
                    try:
                        parsed_response = ast.literal_eval(text_field)
                        if 'content' in parsed_response and isinstance(parsed_response['content'], list):
                            response_text = parsed_response['content'][0].get('text', text_field)
                        else:
                            response_text = text_field
                    except:
                        response_text = text_field
                else:
                    response_text = text_field
            else:
                response_text = str(response)
        else:
            response_text = str(response)
            
        print(f"📝 Extracted text: {response_text}")
        
        # Clean and parse JSON
        json_text = response_text.strip()
        
        # Remove markdown if present
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        # Parse JSON
        parsed_json = json.loads(json_text)
        print(f"✅ JSON parsing successful!")
        print(f"🔍 Parsed keys: {list(parsed_json.keys())}")
        
        # Validate with Satya
        user = SimpleUser(**parsed_json)
        print(f"✅ Satya validation successful!")
        print(f"👤 Validated user:")
        print(f"   Name: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   Age: {user.age}")
        print(f"   Username: {user.username}")
        print(f"   ID: {user.user_id}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📝 Raw text: {json_text}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_anthropic())
