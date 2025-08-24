import os
import sys
import json
import base64
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# Prefer local source in development for consistency
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    import dotenv  # type: ignore
    dotenv.load_dotenv()
except Exception:
    pass

# Simple stdlib HTTP POST

def http_post(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            return json.loads(err_body)
        except Exception:
            return {"error": f"HTTP {e.code}", "detail": str(e)}
    except Exception as e:
        return {"error": str(e)}


def b64_image(path: str) -> (str, str):
    ext = os.path.splitext(path)[1].lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime


PROMPT = "Describe this image in one concise sentence."


def run_anthropic(image_path: str) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"provider": "anthropic", "ok": False, "error": "Missing ANTHROPIC_API_KEY"}

    data_b64, mime = b64_image(image_path)
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": os.getenv("BHUMI_ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        "max_tokens": 128,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": data_b64,
                        },
                    },
                ],
            }
        ],
    }
    resp = http_post(url, payload, headers)
    # Extract text
    text = None
    try:
        text = resp.get("content", [{}])[0].get("text")
    except Exception:
        pass
    return {"provider": "anthropic", "ok": text is not None, "text": text, "raw": resp}


def run_gemini(image_path: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"provider": "gemini", "ok": False, "error": "Missing GEMINI_API_KEY"}

    data_b64, mime = b64_image(image_path)
    model = os.getenv("BHUMI_GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": mime, "data": data_b64}},
                ],
            }
        ]
    }
    resp = http_post(url, payload, headers)
    # Extract text
    text = None
    try:
        parts = resp.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for p in parts:
            if "text" in p:
                text = p["text"]
                break
    except Exception:
        pass
    return {"provider": "gemini", "ok": text is not None, "text": text, "raw": resp}


def main():
    # Default image: assets/bhumi_logo.png (simple placeholder)
    default_image = os.path.join(ROOT, "assets", "bhumi_logo.png")
    image_path = sys.argv[1] if len(sys.argv) > 1 else default_image
    if not os.path.isfile(image_path):
        print(f"Image not found: {image_path}")
        sys.exit(1)

    results = [run_anthropic(image_path), run_gemini(image_path)]

    print("\n=== VLM Describe Smoke Test ===")
    for r in results:
        if r.get("ok"):
            print(f"- {r['provider']}: OK -> {r.get('text')}")
        else:
            print(f"- {r['provider']}: ERROR -> {r.get('error') or r.get('raw')}")


if __name__ == "__main__":
    main()
