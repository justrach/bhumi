import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import json

# Simple weather tool function
async def get_weather(location: str, unit: str = "f") -> str:
    result = f"The weather in {location} is 75°{unit}"
    print(f"\nTool executed: get_weather({location}, {unit}) -> {result}")
    return result

async def main():
    config = LLMConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini/gemini-1.5-flash-8b",  # Back to the original model
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    # Register the weather tool
    client.register_tool(
        name="get_weather",
        func=get_weather,
        description="Get the current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["c", "f"],
                    "description": "Temperature unit (c for Celsius, f for Fahrenheit)"
                }
            },
            "required": ["location", "unit"],
            "additionalProperties": False
        }
    )
    
    # Add system instruction for Gemini
    system_message = {
        "role": "system",
        "content": "You are a helpful weather assistant. Use the get_weather function to check the weather for locations."
    }
    
    # Test queries
    test_queries = [
        "What's the weather like in San Francisco?",
        "How hot is it in Miami?",
        "Tell me the temperature in New York City"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            response = await client.completion([
                system_message,
                {"role": "user", "content": query}
            ])
            print(f"Response: {response['text']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main()) 