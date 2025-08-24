import os
import sys
import asyncio
import argparse
from typing import Dict, Any, Optional

# Prefer local source in development
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    import dotenv  # type: ignore
    dotenv.load_dotenv()
except Exception:
    pass

from bhumi.base_client import BaseLLMClient, LLMConfig

DEFAULT_PROMPT = "Describe this image in one concise sentence."
DEFAULT_IMAGE = os.path.join(ROOT, "assets", "bhumi_logo.png")

MODELS = {
    "anthropic": os.getenv("BHUMI_ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
    "gemini": os.getenv("BHUMI_GEMINI_MODEL", "gemini-2.5-flash"),
}

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
}

BASE_URLS: Dict[str, Optional[str]] = {
    # Anthropic and Gemini base URLs are auto-set internally
    "anthropic": None,
    "gemini": None,
}

async def run_provider(provider: str, prompt: str, image_path: str) -> Dict[str, Any]:
    api_key = API_KEYS.get(provider)
    if not api_key:
        return {"provider": provider, "ok": False, "error": f"Missing API key env for {provider}"}

    if not os.path.isfile(image_path):
        return {"provider": provider, "ok": False, "error": f"Image not found: {image_path}"}

    model = MODELS[provider]
    base_url = BASE_URLS.get(provider)

    model_id = f"{provider}/{model}"
    cfg = LLMConfig(
        api_key=api_key,
        model=model_id,
        base_url=base_url,
        debug=True,
    )
    client = BaseLLMClient(cfg, debug=True)

    try:
        resp = await client.analyze_image(prompt=prompt, image_path=image_path)
        return {"provider": provider, "ok": True, "text": str(resp.get("text") or ""), "raw": resp.get("raw_response")}
    except Exception as e:
        return {"provider": provider, "ok": False, "error": str(e)}

async def main():
    parser = argparse.ArgumentParser(description="Bhumi VLM image description smoke test (Anthropic & Gemini)")
    parser.add_argument("--image", dest="image", default=DEFAULT_IMAGE, help="Path to the image file")
    parser.add_argument("--prompt", dest="prompt", default=DEFAULT_PROMPT, help="Prompt to send along with the image")
    args = parser.parse_args()

    providers = ["anthropic", "gemini"]
    results = await asyncio.gather(*(run_provider(p, args.prompt, args.image) for p in providers))

    print("\n=== VLM Smoke Test Results ===")
    for r in results:
        if r.get("ok"):
            print(f"- {r['provider']}: OK -> {r.get('text')}")
        else:
            print(f"- {r['provider']}: ERROR -> {r.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
