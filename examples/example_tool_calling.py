import asyncio
import os
import sys
import json

# Prefer local source in development
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

from bhumi.base_client import BaseLLMClient, LLMConfig

# Example weather tool function
async def get_weather(location: str, unit: str = "f") -> str:
    result = f"The weather in {location} is 75°{unit}"
    print(f"\nTool executed: get_weather({location}, {unit}) -> {result}")
    return result

async def main():
    config = LLMConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini/gemini-2.5-flash",  # Let's use standard gpt-4 for testing
        # debug=True
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
    
    print("\nStarting weather query test...")
    
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]
    
    print(f"\nSending messages: {json.dumps(messages, indent=2)}")
    # Print tool schema
    print("\nAnthropic tool defs:")
    try:
        print(json.dumps(client.tool_registry.get_anthropic_definitions(), indent=2))
    except Exception as e:
        print(f"(could not get defs) {e}")
    
    try:
        response = await client.completion(messages, debug=True)
        print(f"\nFinal Response (raw): {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"\nError during completion: {e}")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main()) 