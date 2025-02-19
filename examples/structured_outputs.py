import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
from satya import Model, Field
from typing import List, Optional, Literal
import os
import json
from datetime import datetime
from satya.openai import OpenAISchema

class Address(Model):
    """User address information"""
    street: str = Field(description="Street address")
    city: str = Field(description="City name")
    state: str = Field(description="State or province")
    country: str = Field(description="Country name")
    postal_code: str = Field(description="Postal/ZIP code")

class Subscription(Model):
    """User subscription details"""
    plan: Literal["free", "basic", "premium"] = Field(description="Subscription plan type")
    status: Literal["active", "expired", "cancelled"] = Field(description="Current subscription status")
    start_date: datetime = Field(description="When the subscription started")
    end_date: Optional[datetime] = Field(None, description="When the subscription ends/ended")

class UserProfile(Model):
    """Complete user profile information"""
    user_id: str = Field(pattern="^usr_[a-zA-Z0-9]+$", description="Unique user ID")
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: str = Field(pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", description="Email address")
    full_name: str = Field(min_length=1, description="Full name")
    age: int = Field(ge=13, le=120, description="User age")
    address: Address = Field(description="User's address")
    subscription: Subscription = Field(description="Subscription information")
    created_at: datetime = Field(description="Account creation timestamp")

async def main():
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        debug=True,
        extra_config={
            "response_format": OpenAISchema.response_format(UserProfile, "user_profile")
        }
    )
    
    client = BaseLLMClient(config)
    
    test_queries = [
        "Get me the user profile for John Doe",
        "Show me the profile of a premium user",
        "Find a user from New York",
        "Get me details of a recently created account"
    ]
    
    validator = UserProfile.validator()
    validator.set_batch_size(10)  # Adjust batch size as needed
    
    def clean_json_response(text: str) -> str:
        """Clean JSON response by removing markdown code blocks"""
        # Remove markdown code blocks if present
        if text.startswith("```") and text.endswith("```"):
            # Split by newline and remove first and last lines (```json and ```)
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return text
    
    for query in test_queries:
        print(f"\n\nQuery: {query}")
        try:
            response = await client.completion([
                {"role": "system", "content": """You are a user database assistant.
                    When asked about users, generate a realistic user profile.
                    Return a single JSON object matching the schema.
                    Make sure all dates are in ISO format (YYYY-MM-DDTHH:MM:SS).
                    Do not wrap the response in markdown code blocks."""},
                {"role": "user", "content": query}
            ])
            
            try:
                # Parse and validate the response using Satya
                print("\nRaw Response:")
                print(response["text"])
                
                # Clean and parse the response
                cleaned_response = clean_json_response(response["text"])
                
                # Validate using Satya's streaming validator
                for validated in validator.validate_stream([json.loads(cleaned_response)]):
                    user_data = validated
                    print("\nValidated User Profile:")
                    print(json.dumps(user_data, indent=2, default=str))
                    
                    # Save profile to file
                    filename = f"user_profile_{user_data['user_id']}.json"
                    with open(filename, "w") as f:
                        json.dump(user_data, f, indent=2, default=str)
                    print(f"\nProfile saved to {filename}")
                
            except Exception as e:
                print(f"\nFailed to validate response: {e}")
                print("Cleaned response:")
                print(cleaned_response)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main()) 