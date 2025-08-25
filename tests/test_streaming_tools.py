import sys
from pathlib import Path
import asyncio
import json
import pytest

# Ensure local src is importable with highest priority (before site-packages)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bhumi.base_client import BaseLLMClient, LLMConfig


class MockCore:
    """
    Minimal mock of BhumiCore for streaming tests.
    Drives two-round streaming:
    - Round 1: emits tool_call deltas and finish_reason=tool_calls
    - Round 2: emits content deltas and completes
    """

    def __init__(self):
        # Each submission selects the next sequence
        self.submission_index = -1
        self.sequences = [
            # Round 1: tool call accumulation then tool_calls finish
            [
                json.dumps(
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "call_1",
                                            "type": "function",
                                            "function": {"name": "get_time"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ),
                json.dumps(
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "function": {"arguments": '{"tz": "UTC"}'}
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ),
                json.dumps(
                    {
                        "choices": [
                            {
                                "delta": {},
                                "finish_reason": "tool_calls",
                            }
                        ]
                    }
                ),
            ],
            # Round 2: final assistant content
            [
                json.dumps(
                    {
                        "choices": [
                            {
                                "delta": {"content": "It is 12:00 in UTC.\n"},
                            }
                        ]
                    }
                ),
                json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]}),
            ],
        ]
        self._cursor = 0

    def _submit(self, payload: str) -> None:
        # Move to next sequence and reset cursor
        self.submission_index += 1
        self._cursor = 0
        print(f"MockCore: submit called -> submission_index={self.submission_index}")

    def _get_stream_chunk(self):
        # Return next chunk or [DONE]
        if 0 <= self.submission_index < len(self.sequences):
            seq = self.sequences[self.submission_index]
            if self._cursor < len(seq):
                ch = seq[self._cursor]
                self._cursor += 1
                print(f"MockCore: emitting chunk {self._cursor}/{len(seq)} from round {self.submission_index}")
                return ch
        print("MockCore: [DONE]")
        return "[DONE]"


@pytest.mark.asyncio
async def test_streaming_with_tool_calls_afc_like():
    # Setup client with mock core
    cfg = LLMConfig(api_key="test", model="openai/gpt-4o-mini")
    client = BaseLLMClient(cfg, debug=True)
    client.core = MockCore()

    # Register tool
    tool_called = {"count": 0, "last_tz": None}

    async def get_time(tz: str = "UTC") -> str:
        tool_called["count"] += 1
        tool_called["last_tz"] = tz
        return f"12:00 in {tz}"

    client.register_tool(
        name="get_time",
        func=get_time,
        description="Get the current time for a timezone.",
        parameters={
            "type": "object",
            "properties": {"tz": {"type": "string"}},
            "required": [],
            "additionalProperties": False,
        },
    )

    messages = [{"role": "user", "content": "What time is it?"}]

    # Collect streamed output
    chunks = []

    stream = await client.completion(messages, stream=True)
    async for chunk in stream:
        chunks.append(chunk)

    # Assertions
    assert tool_called["count"] == 1, "Tool should be invoked once during streaming AFC"
    assert tool_called["last_tz"] == "UTC"
    output = "".join(chunks)
    assert "UTC" in output and "12:00" in output
