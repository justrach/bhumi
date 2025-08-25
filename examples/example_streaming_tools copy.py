import asyncio
import os
from typing import Any, Dict

from bhumi.base_client import BaseLLMClient, LLMConfig


async def main() -> None:
    # Configure provider/model and API key from env
    # Default to an OpenAI-compatible model that supports tools out-of-the-box.
    model = os.environ.get("BHUMI_MODEL")
    api_key = None

    if not model:
        if os.environ.get("OPENAI_API_KEY"):
            model = "openai/gpt-4o-mini"
            api_key = os.environ.get("OPENAI_API_KEY")
        elif os.environ.get("GROQ_API_KEY"):
            model = "groq/moonshotai/kimi-k2-instruct"
            api_key = os.environ.get("GROQ_API_KEY")
        elif os.environ.get("ANTHROPIC_API_KEY"):
            # Use a tools-capable Anthropic model
            model = "anthropic/claude-3-5-haiku-20241022"
            api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Final API key resolution if not already set
    api_key = api_key or (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("SAMBANOVA_API_KEY")
        or os.environ.get("CEREBRAS_API_KEY")
        or "sk-placeholder"  # Replace with a real key or set env vars
    )

    # Fallback model if still unset
    if not model:
        model = "openai/gpt-4o-mini"

    cfg = LLMConfig(api_key=api_key, model=model)
    client = BaseLLMClient(cfg, debug=True)

    # Register a simple tool
    async def get_time(tz: str = "UTC") -> str:
        # Replace with real impl; demo returns fixed value
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

    # Ask a question that should invoke the tool
    messages = [
        {"role": "user", "content": "What time is it now? Use the get_time tool for UTC, then answer."}
    ]

    # Warn if an Anthropic model without tool support was chosen
    if model.startswith("anthropic/") and "claude-3-5" not in model:
        print("[warn] Selected Anthropic model may not support tool-use; consider a claude-3-5-* model.")

    stream = await client.completion(messages, stream=True)
    print("--- Streaming output start ---")
    async for chunk in stream:
        print(chunk, end="", flush=True)
    print("\n--- Streaming output end ---")


if __name__ == "__main__":
    asyncio.run(main())
