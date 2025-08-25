import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

import dotenv
from bhumi.base_client import BaseLLMClient, LLMConfig


dotenv.load_dotenv()


def prompt_tz() -> str:
    try:
        tz = input("Enter timezone to check (default: UTC): ").strip()
        return tz or "UTC"
    except Exception:
        return "UTC"


async def main(tz: str) -> None:
    api_key = os.environ.get("OPENAI_API_KEY") or "sk-placeholder"

    # OpenAI-compatible model that supports tool calling and streaming
    cfg = LLMConfig(api_key=api_key, model="openai/gpt-4o-mini")
    client = BaseLLMClient(cfg)  # no debug noise

    # Capture the last tool result so we can craft a clean final sentence
    tool_last = {"value": None}

    async def get_time(tz: str = "UTC") -> str:
        # Placeholder logic; replace with real time lookup if desired
        result = f"12:00 in {tz}"
        tool_last["value"] = result
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
            "additionalProperties": True,
        },
    )

    messages = [
        {
            "role": "user",
            "content": f"Please tell me the current time. Use the get_time tool for {tz}, then reply in one short sentence.",
        }
    ]

    print(f"\nOkay — I’ll look up the time in {tz} and respond in one sentence.\n")

    stream = await client.completion(messages, stream=True)
    print("--- Streaming ---")
    chunks: list[str] = []

    # Helper to type text out character-by-character
    async def type_out(text: str, delay: float = 0.02) -> None:
        for ch in text:
            print(ch, end="", flush=True)
            await asyncio.sleep(delay)

    # Stream and animate characters as they arrive
    async for chunk in stream:
        if chunk:
            chunks.append(chunk)
            await type_out(chunk)
    print("\n--- Done ---")

    typed_fallback = False
    final_text = "".join(chunks).strip()
    if not final_text:
        # No streamed chunks arrived — do a non-stream completion and type it out so it still feels live
        try:
            resp = await client.completion(messages, stream=False)
            final_text = (resp.get("text") if isinstance(resp, dict) else str(resp)) or ""
        except Exception:
            final_text = ""

        if final_text:
            print("\n--- Fallback typing ---")
            await type_out(final_text)
            print("\n--- Done ---")
            typed_fallback = True
        else:
            # Last-resort sentence if we have only tool output
            if tool_last["value"]:
                final_text = f"According to my tools, it's {tool_last['value']}."
            else:
                final_text = f"I couldn't get a response just now, but try again and I'll check {tz} for you."

    # Save a transcript file so the run feels interactive
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / f"interactive_session_{ts}.txt"
    transcript = {
        "tz": tz,
        "messages": messages,
        "tool_result": tool_last["value"],
        "final_text": final_text,
        "created_at": ts,
    }
    try:
        out_path.write_text(json.dumps(transcript, indent=2))
        print(f"\nSaved transcript to {out_path}")
    except Exception as e:
        print(f"\n(Note: could not save transcript: {e})")

    # Avoid duplicating the text when we already typed it in fallback
    if not typed_fallback:
        print(f"\nFinal: {final_text}\n")


if __name__ == "__main__":
    tz = prompt_tz()
    asyncio.run(main(tz))
