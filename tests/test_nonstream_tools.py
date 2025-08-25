import sys
from pathlib import Path
import asyncio
import json
import pytest

# Ensure local src is importable first
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import bhumi.base_client as bc
from bhumi.base_client import BaseLLMClient, LLMConfig


class MockCoreNonStream:
    """
    Drives two-round non-streaming flow:
    - Round 1 (submit #1): returns a response containing tool_calls (OpenAI shape)
    - Round 2 (submit #2): returns a final assistant message
    """

    def __init__(self):
        self.submission_index = -1
        self.responses = [
            # First non-stream response with tool_calls
            json.dumps(
                {
                    "id": "cmpl_1",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "gpt-x",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "get_time",
                                            "arguments": '{"tz": "UTC"}'
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "prompt_tokens_details": {"cached_tokens": 0, "audio_tokens": 0},
                        "completion_tokens_details": {
                            "reasoning_tokens": 0,
                            "audio_tokens": 0,
                            "accepted_prediction_tokens": 0,
                            "rejected_prediction_tokens": 0,
                        },
                    },
                    "service_tier": "default",
                }
            ),
            # Second non-stream response with final content
            json.dumps(
                {
                    "id": "cmpl_2",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "gpt-x",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "It is 12:00 in UTC.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "prompt_tokens_details": {"cached_tokens": 0, "audio_tokens": 0},
                        "completion_tokens_details": {
                            "reasoning_tokens": 0,
                            "audio_tokens": 0,
                            "accepted_prediction_tokens": 0,
                            "rejected_prediction_tokens": 0,
                        },
                    },
                    "service_tier": "default",
                }
            ),
        ]

    def _submit(self, payload: str) -> None:
        self.submission_index += 1

    def _get_response(self):
        if 0 <= self.submission_index < len(self.responses):
            # Serve exactly one response per submission
            idx = self.submission_index
            # Prevent re-serving
            self.submission_index = len(self.responses)
            return self.responses[idx]
        return None


@pytest.mark.asyncio
async def test_nonstream_afc_openai_like_tool_calls():
    cfg = LLMConfig(api_key="test", model="openai/gpt-x")
    # Monkeypatch Rust core to avoid real initialization
    bc._rust = type("_MockRust", (), {"BhumiCore": lambda *args, **kwargs: MockCoreNonStream()})
    client = BaseLLMClient(cfg)
    # Core already mocked by constructor; ensure interface present

    # Track tool invocation
    invoked = {"count": 0, "tz": None}

    async def get_time(tz: str = "UTC") -> str:
        invoked["count"] += 1
        invoked["tz"] = tz
        return f"12:00 in {tz}"

    client.register_tool(
        name="get_time",
        func=get_time,
        description="Get time",
        parameters={
            "type": "object",
            "properties": {"tz": {"type": "string"}},
            "required": [],
            "additionalProperties": False,
        },
    )

    messages = [{"role": "user", "content": "What time is it?"}]
    resp = await client.completion(messages)

    assert invoked["count"] == 1
    assert invoked["tz"] == "UTC"
    assert isinstance(resp, dict)
    assert "UTC" in resp.get("text", "")
