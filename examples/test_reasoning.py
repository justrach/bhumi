import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import json

# Example weather tool function
async def get_weather(location: str, unit: str = "f") -> str:
    result = f"The weather in {location} is 35°{unit}, the weather in Boston is 35°{unit}"
    print(f"\nTool executed: get_weather({location}, {unit}) -> {result}")
    return result

async def main():
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model="groq/deepseek-r1-distill-qwen-32b",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    # Register the weather tool
    client.register_tool(
        name="get_weather",  # Match the name the model expects
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
    
    test_queries = [
        "What's the weather like in San Francisco in F?",
        "Tell me the temperature in Boston in Celsius"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            response = await client.completion([
                {"role": "user", "content": query}
            ])
            # Check response type and handle accordingly
            if hasattr(response, 'think'):
                # Reasoning model response
                print("\nReasoning:")
                print(response.think)
                print("\nResponse:")
                print(response)
            elif isinstance(response, dict):
                # Tool call or regular response
                if "tool_calls" in response:
                    print("\nTool Calls:")
                    print(response["tool_calls"])
                print("\nResponse:")
                print(response["text"])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main()) 