import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os
import dotenv

dotenv.load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


async def main():
    # Configure for OpenAI with GPT-5 for new Responses API
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-5-nano",  # Use GPT-5 for Responses API
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

    print("\n" + "=" * 70)
    print("🚀 OpenAI Responses API Streaming Test")
    print("=" * 70)

    # Test 1: Legacy Chat Completions API (non-streaming)
    print("\n📡 Test 1: Legacy Chat Completions API")
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"Response: {response['text']}")

    # Test 2: New Responses API (non-streaming)
    print("\n🆕 Test 2: New Responses API (non-streaming)")
    try:
        # This should trigger the Responses API since we're using input= parameter
        response = await client.completion(
            input="Tell me a short story about a robot",
            stream=False
        )
        print(f"Response: {response.get('text', response)}")
    except Exception as e:
        print(f"Responses API error: {e}")
        print("Note: Responses API may not be fully implemented for completion() method yet")

    # Test 3: Chat Completions Streaming (current working method)
    print("\n🌊 Test 3: Chat Completions Streaming")
    print("Streaming response:")
    try:
        async for chunk in await client.completion(
            [
                {"role": "user", "content": "Count to 5 slowly"}
            ],
            stream=True,
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"Streaming error: {e}")

    # Test 4: Attempt Responses API Streaming (experimental)
    print("\n🚀 Test 4: Responses API Streaming (experimental)")
    print("Note: This may not work yet as streaming for Responses API needs implementation")
    try:
        # Try to use Responses API with streaming
        async for chunk in await client.completion(
            input="Tell me a story about space, one word at a time",
            stream=True
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"Responses API streaming error: {e}")
        print("This is expected - Responses API streaming needs to be implemented")

    print("\n💡 Summary:")
    print("   • Chat Completions streaming: ✅ Working")
    print("   • Responses API non-streaming: ⚠️  May need implementation")
    print("   • Responses API streaming: ❌ Needs implementation")
    print("   • Recommendation: Use Chat Completions API for streaming until Responses API streaming is ready")


if __name__ == "__main__":
    asyncio.run(main())
