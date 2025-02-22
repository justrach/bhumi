import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import dotenv

dotenv.load_dotenv()

api_key = os.getenv("SAMBANOVA_API_KEY")

async def main():
    # Configure for SambaNova
    config = LLMConfig(
        api_key=api_key,
        model="sambanova/Meta-Llama-3.1-70B-Instruct",
        debug=True, max_retries=3
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
        {"role": "user", "content": "Write a 500 word haiku about AI"}
    ], stream=True):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main()) 