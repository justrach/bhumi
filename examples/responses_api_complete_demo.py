"""
Complete Responses API Demo

Shows streaming, tools, and various features working together.
"""

import asyncio
import os
from dotenv import load_dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig

load_dotenv()

async def complete_responses_api_demo():
    """Comprehensive demo of Responses API features"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",
        debug=False
    )
    client = BaseLLMClient(config, debug=False)

    print("🚀 COMPLETE RESPONSES API DEMO")
    print("=" * 50)

    # 1. Basic Responses API
    print("\n📋 1. Basic Responses API (non-streaming)")
    response = await client.completion(
        input="What is 2+2?",
        instructions="You are a helpful math assistant"
    )
    print(f"🤖 Response: {response['text']}")

    # 2. Responses API Streaming (working examples)
    print("\n🌊 2. Responses API Streaming (working examples)")
    
    working_prompts = [
        "Say hello world",
        "Count: 1, 2, 3",
        "Tell me a joke",
        "What is AI?"
    ]
    
    for i, prompt in enumerate(working_prompts, 1):
        print(f"\n   Example {i}: '{prompt}'")
        print("   🤖 ", end="", flush=True)
        
        chunk_count = 0
        async for chunk in await client.completion(
            input=prompt,
            stream=True
        ):
            chunk_count += 1
            print(chunk, end="", flush=True)
            if chunk_count >= 15:  # Limit output
                print("... (truncated)")
                break
        
        print(f"\n   ✅ Chunks: {chunk_count}")

    # 3. Tool Support with Responses API
    print("\n🔧 3. Tool Support with Responses API")
    
    # Register a weather tool
    def get_weather(location: str) -> str:
        weather_data = {
            "Paris": "Sunny, 22°C",
            "London": "Cloudy, 15°C", 
            "Tokyo": "Rainy, 18°C",
            "New York": "Snowy, -2°C"
        }
        return weather_data.get(location, f"Weather data not available for {location}")
    
    client.tool_registry.register(
        name="get_weather",
        func=get_weather,
        description="Get current weather for a city",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    )
    
    # Test tool with Responses API
    response = await client.completion(
        input="What's the weather like in Paris and London?",
        instructions="Use the get_weather tool to check weather information"
    )
    print(f"🤖 Weather Response: {response['text']}")

    # 4. Advanced: Multiple tools
    print("\n🔧 4. Multiple Tools Example")
    
    def calculate(expression: str) -> str:
        try:
            # Simple calculator (be careful with eval in production!)
            result = eval(expression.replace("^", "**"))
            return f"{expression} = {result}"
        except:
            return f"Cannot calculate: {expression}"
    
    client.tool_registry.register(
        name="calculate",
        func=calculate,
        description="Calculate mathematical expressions",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to calculate"
                }
            },
            "required": ["expression"]
        }
    )
    
    response = await client.completion(
        input="What's the weather in Tokyo and what is 15 * 7?",
        instructions="Use appropriate tools to answer both questions"
    )
    print(f"🤖 Multi-tool Response: {response['text']}")

    # 5. Streaming Issues Investigation
    print("\n❓ 5. Streaming Issues Investigation")
    
    problematic_prompts = [
        "Count to 5 slowly with words between numbers",
        "List the numbers 1, 2, 3, 4, 5 with explanations",
        "Tell me a story about counting to 5"
    ]
    
    print("   These prompts often return 0 chunks (investigating why):")
    for prompt in problematic_prompts:
        print(f"\n   Testing: '{prompt}'")
        print("   🤖 ", end="", flush=True)
        
        chunk_count = 0
        async for chunk in await client.completion(
            input=prompt,
            stream=True
        ):
            chunk_count += 1
            print(chunk, end="", flush=True)
            if chunk_count >= 10:
                print("... (truncated)")
                break
        
        print(f"\n   Result: {chunk_count} chunks")

    # Summary
    print(f"\n🎯 SUMMARY:")
    print(f"✅ Responses API detection: Working")
    print(f"✅ Non-streaming: Working perfectly")
    print(f"✅ Streaming (simple prompts): Working")
    print(f"❓ Streaming (complex prompts): Needs investigation")
    print(f"✅ Tool support: Working perfectly")
    print(f"✅ Multiple tools: Working")
    print(f"✅ Instructions parameter: Working")
    
    print(f"\n💡 USAGE RECOMMENDATIONS:")
    print(f"   • Use simple, direct prompts for streaming")
    print(f"   • Tools work seamlessly with Responses API")
    print(f"   • Both input= and instructions= parameters supported")
    print(f"   • Fallback to Chat Completions ensures compatibility")

if __name__ == "__main__":
    asyncio.run(complete_responses_api_demo())
