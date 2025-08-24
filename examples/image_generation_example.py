#!/usr/bin/env python3
"""
Example: Image generation via OpenAI-compatible v1 images API.

Requires an API key and model like `openai/gpt-image-1` or any provider that
exposes an OpenAI-compatible images endpoint.

Usage:
    export OPENAI_API_KEY=...  # or provider-specific key
    python examples/image_generation_example.py
"""
import os
import base64
from pathlib import Path
from typing import Optional

from bhumi.base import LLMConfig
from bhumi.providers.openai_client import OpenAILLM


def save_b64_image(b64: str, out: Path) -> None:
    out.write_bytes(base64.b64decode(b64))
    print(f"Saved: {out}")


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Set OPENAI_API_KEY to run this example.")
        return

    # Choose an image-capable model; adjust as needed
    model = os.environ.get("IMAGE_MODEL", "openai/gpt-image-1")

    cfg = LLMConfig(api_key=api_key, model=model)
    client = OpenAILLM(cfg)

    prompt = "A watercolor painting of a sunrise over rolling hills, high detail"
    print(f"Generating image for prompt: {prompt}")

    resp = client.generate_image  # method is async in BaseLLMClient; wrapper forwards

    # Run in a simple async runner
    import asyncio

    async def run():
        data = await client.generate_image(prompt=prompt, size="512x512", n=1)
        # Expecting OpenAI-like response: { "data": [ { "b64_json": "..." } ] }
        images = data.get("data", [])
        if not images:
            print("No image returned:", data)
            return
        b64 = images[0].get("b64_json")
        if not b64:
            print("No b64_json found in response:", data)
            return
        out = Path("image_example.png")
        save_b64_image(b64, out)

    asyncio.run(run())


if __name__ == "__main__":
    main()
