import asyncio
import os
import dotenv
from bhumi.base import LLMConfig, create_llm

dotenv.load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

async def main():
    # Configure for Claude
    config = LLMConfig(
        api_key=API_KEY,
        model="anthropic/claude-3-haiku-20240307",
        debug=False  # Set to True to see request/response details
    )
    
    client = create_llm(config)
    
    # Test regular completion
    print("\nTesting regular completion:")
    response = await client.completion([
        {"role": "user", "content": "Write a haiku about artificial intelligence"}
    ])
    print(f"\nResponse: {response['text']}")
    
    # Test streaming
    print("\nTesting streaming completion:")
    print("Streaming response:\n")
    async for chunk in await client.completion([
        {"role": "user", "content": "Tell me a short story about a robot learning to love, word by word"}
    ], stream=True):
        print(chunk, end="", flush=True)
    print("\n")
    
    # Test with system message
    print("\nTesting with system message:")
    response = await client.completion([
        {"role": "system", "content": "You are a helpful AI assistant that speaks in rhyming verse"},
        {"role": "user", "content": "What's the weather like today?"}
    ])
    print(f"\nResponse: {response['text']}")

if __name__ == "__main__":
    asyncio.run(main()) 