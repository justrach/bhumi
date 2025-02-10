import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import dotenv

dotenv.load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

async def main():
    # Configure for Groq
    config = LLMConfig(
        api_key=api_key,
        model="groq/mixtral-8x7b-32768",
        debug=True,
        max_retries=3,
        max_tokens=500
    )
    
    client = BaseLLMClient(config, debug=True)
    
    # Test completion
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"\nResponse: {response['text']}")
    
    # Test streaming
    print("\nStreaming response:")
    async for chunk in await client.completion([
        {"role": "user", "content": "Write a haiku about AI"}
    ], stream=True):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main()) 