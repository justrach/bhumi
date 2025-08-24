import os
import sys

# Prefer local source in development
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)
import asyncio
from typing import Optional, Dict, Any

try:
    import dotenv  # type: ignore
    dotenv.load_dotenv()
except Exception:
    pass

from bhumi.base_client import BaseLLMClient, LLMConfig

PROMPT = "Give me one fun fact in <=20 words."

# You can tweak models here if you prefer different variants
MODELS = {
    "anthropic": os.getenv("BHUMI_ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
    "gemini": os.getenv("BHUMI_GEMINI_MODEL", "gemini-2.0-flash"),
    "groq": os.getenv("BHUMI_GROQ_MODEL", "llama-3.1-8b-instant"),
    "cerebras": os.getenv("BHUMI_CEREBRAS_MODEL", "llama3.1-8b"),
}

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
    "groq": os.getenv("GROQ_API_KEY"),
    "cerebras": os.getenv("CEREBRAS_API_KEY"),
}

BASE_URLS: Dict[str, Optional[str]] = {
    # Anthropic and Gemini base URLs are auto-set internally
    "anthropic": None,
    "gemini": None,  # uses OpenAI-compatible /openai endpoint internally
    "groq": None,    # uses OpenAI-compatible path
    # Cerebras needs explicit base_url
    "cerebras": os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"),
}

async def run_provider(provider: str) -> Dict[str, Any]:
    api_key = API_KEYS.get(provider)
    if not api_key:
        return {"provider": provider, "error": f"Missing API key env for {provider}"}

    model = MODELS[provider]
    base_url = BASE_URLS.get(provider)

    cfg = LLMConfig(
        api_key=api_key,
        model=f"{provider}/{model}",
        base_url=base_url,
        debug=True,
    )
    client = BaseLLMClient(cfg, debug=True)

    try:
        resp = await client.completion([
            {"role": "user", "content": PROMPT}
        ], debug=True)
        return {"provider": provider, "ok": True, "text": resp.get("text", "")[:200]}
    except Exception as e:
        return {"provider": provider, "ok": False, "error": str(e)}

async def main():
    providers = ["anthropic", "gemini", "groq", "cerebras"]
    results = await asyncio.gather(*(run_provider(p) for p in providers))
    print("\n=== Smoke Test Results ===")
    for r in results:
        if r.get("ok"):
            print(f"- {r['provider']}: OK -> {r.get('text')}")
        else:
            print(f"- {r['provider']}: ERROR -> {r.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
