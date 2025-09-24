"""
Mistral AI Example with Bhumi

Demonstrates:
- Basic chat completions
- Function calling
- Image analysis (with vision models)
- Streaming responses

Usage:
    export MISTRAL_API_KEY=your_mistral_api_key
    python examples/mistral_example.py
"""
import dotenv
dotenv.load_dotenv()
import asyncio
import os
from bhumi.base_client import BaseLLMClient, LLMConfig

async def main():
    # Check for API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return

    print("🤖 Mistral AI Examples with Bhumi")
    print("=" * 50)

    # 1. Basic Chat Completion
    print("\n1️⃣ Basic Chat Completion")
    config = LLMConfig(
        api_key=api_key,
        model="mistral/mistral-small-latest"
    )
    client = BaseLLMClient(config)

    response = await client.completion([
        {"role": "user", "content": "Bonjour! Can you tell me about Paris in French?"}
    ])
    print(f"Response: {response['text']}")

    # 2. Function Calling
    print("\n2️⃣ Function Calling")
    
    def get_weather(location: str) -> str:
        """Get weather for a location"""
        return f"The weather in {location} is sunny and 22°C"
    
    def calculate(expression: str) -> str:
        """Calculate mathematical expressions"""
        try:
            result = eval(expression.replace("^", "**"))
            return f"{expression} = {result}"
        except:
            return f"Cannot calculate: {expression}"

    # Register tools
    client.tool_registry.register(
        name="get_weather",
        func=get_weather,
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"]
        }
    )

    client.tool_registry.register(
        name="calculate",
        func=calculate,
        description="Calculate mathematical expressions",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"}
            },
            "required": ["expression"]
        }
    )

    # Test function calling
    response = await client.completion([
        {"role": "system", "content": "You are a helpful assistant with access to weather and calculator tools."},
        {"role": "user", "content": "What's the weather in Lyon and what is 15 * 7?"}
    ])
    print(f"Tool response: {response['text']}")

    # 3. Streaming
    print("\n3️⃣ Streaming Response")
    print("Streaming: ", end="", flush=True)
    
    async for chunk in await client.completion([
        {"role": "user", "content": "Write a short poem about the French Riviera"}
    ], stream=True):
        print(chunk, end="", flush=True)
    print()  # New line after streaming

    # 4. Vision (if vision model is available)
    print("\n4️⃣ Vision Analysis")
    try:
        vision_config = LLMConfig(
            api_key=api_key,
            model="mistral/pixtral-12b-2409"  # Mistral's vision model
        )
        vision_client = BaseLLMClient(vision_config)

        # Simple test image (1x1 red pixel)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        response = await vision_client.completion([
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{test_image_b64}"}}
                ]
            }
        ])
        print(f"Vision response: {response['text']}")
        
    except Exception as e:
        print(f"Vision model not available or error: {e}")

    # 5. Structured Output (via prompt engineering)
    print("\n5️⃣ Structured Output")
    response = await client.completion([
        {"role": "system", "content": "You are a helpful assistant that responds in valid JSON format."},
        {"role": "user", "content": "Create a JSON profile for Marie Curie with fields: name, profession, nationality, famous_for. Respond only with JSON."}
    ])
    print(f"JSON response: {response['text']}")

    print("\n✅ All Mistral examples completed!")

if __name__ == "__main__":
    asyncio.run(main())
