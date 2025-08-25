import asyncio
import os
import dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig


dotenv.load_dotenv()


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY") or "sk-placeholder"

    # OpenAI model that supports tool calling and streaming
    cfg = LLMConfig(api_key=api_key, model="openai/gpt-4o-mini", debug=True)
    client = BaseLLMClient(cfg, debug=True)

    # Debug banner
    model = cfg.model
    provider = model.split("/")[0] if "/" in model else model
    hybrid = os.environ.get("BHUMI_HYBRID_TOOLS", "0")
    redacted = (api_key[:6] + "..." + api_key[-4:]) if api_key and len(api_key) >= 10 else "<none>"
    print(f"[dbg] provider={provider} model={model} hybrid={hybrid} timeout={cfg.timeout} key=OPENAI_API_KEY={redacted}")

    # Register a simple tool to demonstrate AFC-style streaming with tools
    async def get_time(tz: str = "UTC") -> str:
        # Replace with real logic if desired
        return f"12:00 in {tz}"

    client.register_tool(
        name="get_time",
        func=get_time,
        description="Get the current time for a timezone.",
        parameters={
            "type": "object",
            "properties": {
                "tz": {"type": "string", "description": "Timezone name like UTC"}
            },
            "required": [],
            "additionalProperties": False,
        },
    )

    # Ask a question that should invoke the tool, then continue streaming
    messages = [
        {
            "role": "user",
            "content": "What time is it now? Use the get_time tool for UTC, then answer succinctly.",
        }
    ]

    stream = await client.completion(messages, stream=True)
    print("--- Streaming output start (OpenAI + tools) ---")
    async for chunk in stream:
        print(chunk, end="", flush=True)
    print("\n--- Streaming output end ---")


if __name__ == "__main__":
    asyncio.run(main())
