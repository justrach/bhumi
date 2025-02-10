import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import dotenv

dotenv.load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

async def main():
    # Configure for Anthropic
    config = LLMConfig(
        api_key=api_key,
        model="anthropic/claude-3-haiku-20240307",  # Using provider/model format
        debug=True
    )
    
    # Create client with provider set to "anthropic"
    client = BaseLLMClient(config, debug=True)
    
    # Test completion
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"\nResponse: {response['text']}")
    
    # Test streaming
    print("\nStreaming response:")
    async for chunk in await client.completion([
        {"role": "user", "content": "Tell me a joke on my name in less than 50 words"}
    ], stream=True):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main()) 