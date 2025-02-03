import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
async def main():
    # Example with OpenAI-compatible API
    config = LLMConfig(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        model=MODEL,
        provider="openai"
    )
    
    client = BaseLLMClient(config, debug=True)
    
    # Regular completion
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"Regular response: {response['text']}")
    
    # Streaming completion
    # print("\nStreaming response:")
    # async for chunk in client.completion([
    #     {"role": "user", "content": "Tell me a joke"}
    # ], stream=True):
    #     print(chunk, end="", flush=True)
    
    # # Example with custom API endpoint
    # custom_config = LLMConfig(
    #     api_key="your-api-key",
    #     base_url="https://your-custom-endpoint.com/v1",
    #     model="custom-model",
    #     provider="custom"
    # )
    
    # custom_client = BaseLLMClient(custom_config, debug=True)
    # # Use the same interface with your custom endpoint

if __name__ == "__main__":
    asyncio.run(main()) 