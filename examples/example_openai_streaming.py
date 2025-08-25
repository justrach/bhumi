import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import dotenv

dotenv.load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


async def main():
    # Configure for OpenAI
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-4o-mini",  # Provider prefix triggers OpenAI routing
        debug=True,
    )

    client = BaseLLMClient(config, debug=True)

    # Debug banner
    model = config.model
    provider = model.split("/")[0] if "/" in model else model
    hybrid = os.environ.get("BHUMI_HYBRID_TOOLS", "0")
    key_src = "OPENAI_API_KEY" if os.getenv("OPENAI_API_KEY") else "<missing>"
    redacted = (api_key[:6] + "..." + api_key[-4:]) if api_key else "<none>"
    print(f"[dbg] provider={provider} model={model} key={key_src}={redacted} hybrid={hybrid} timeout={config.timeout}")

    # Test completion
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"\nResponse: {response['text']}")

    # Test streaming
    print("\nStreaming response:")
    async for chunk in await client.completion(
        [
            {"role": "user", "content": "Count to 5"}
        ],
        stream=True,
    ):
        print(chunk, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
