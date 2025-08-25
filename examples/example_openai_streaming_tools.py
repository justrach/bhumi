import asyncio
import os
import dotenv
import json
from bhumi.base_client import BaseLLMClient, LLMConfig


dotenv.load_dotenv()


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY") or "sk-placeholder"

    # OpenAI model that supports tool calling and streaming
    cfg = LLMConfig(api_key=api_key, model="openai/gpt-5")
    client = BaseLLMClient(cfg)  # no debug noise

    # Register a simple tool; print when it runs so users can see tool activity
    async def get_time(tz: str = "UTC") -> str:
        result = f"12:00 in {tz}"
        print(f"\nTool executed: get_time({tz}) -> {result}")
        return result

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

    # Mirror example_tool_calling.py display style
    print("\nStarting time query test (OpenAI + tools)...")
    print(f"\nSending messages: {json.dumps(messages, indent=2)}")
    print("\nOpenAI tool defs:")
    try:
        print(json.dumps(client.tool_registry.get_openai_definitions(), indent=2))
    except Exception as e:
        print(f"(could not get defs) {e}")

    stream = await client.completion(messages, stream=True)
    print("\n--- Streaming output start ---")
    chunks: list[str] = []
    async for chunk in stream:
        if chunk:
            chunks.append(chunk)
            print(chunk, end="", flush=True)
    print("\n--- Streaming output end ---")

    final_text = "".join(chunks).strip()
    if not final_text:
        # Fallback: request a non-stream completion so we always show an answer
        try:
            resp = await client.completion(messages, stream=False)
            final_text = (resp.get("text") if isinstance(resp, dict) else str(resp)) or ""
        except Exception as e:
            final_text = f"(no streamed text; fallback failed: {e})"

    print(f"\nFinal: {final_text}\n")


if __name__ == "__main__":
    asyncio.run(main())
