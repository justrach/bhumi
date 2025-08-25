import asyncio
import os
import json
from typing import List, Dict, Any

import dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig


dotenv.load_dotenv()


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY") or "sk-placeholder"

    # A model that supports tools + streaming
    cfg = LLMConfig(api_key=api_key, model="openai/gpt-4o-mini")
    client = BaseLLMClient(cfg,debug=True)

    # Register a tiny tool so we can see tool phases
    async def get_time(tz: str = "UTC") -> str:
        result = f"12:00 in {tz}"
        print(f"\n[tool] get_time({tz}) -> {result}")
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
            "additionalProperties": True,
        },
    )

    # Ask for something a bit longer so streaming is visible
    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                "Use the get_time tool for UTC first. Then, in 3–5 sentences, explain a simple tip "
                "for staying focused at work. Keep it friendly."
            ),
        }
    ]

    print("\n=== Interactive Streaming Demo ===")
    print("Provider: openai  |  Model: gpt-4o-mini  |  Tools: get_time\n")
    print("Messages:")
    print(json.dumps(messages, indent=2))

    stream = await client.completion(messages, stream=True)

    print("\n--- Live ---\n")
    async for chunk in stream:
        if chunk:
            print(chunk, end="", flush=True)
    print("\n\n--- End of stream ---\n")


if __name__ == "__main__":
    asyncio.run(main())
