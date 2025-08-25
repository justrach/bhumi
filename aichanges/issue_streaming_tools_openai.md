# Issue: OpenAI streaming with tools hangs; plain streaming works

- Status: Open
- Area: Rust core streaming (SSE) when tools are provided (OpenAI)
- Reporter: user via examples
- Date: 2025-08-25

## Summary

When using OpenAI with tools enabled, the streaming path hangs (no SSE chunks, eventual Python timeout), while plain streaming (no tools) works fine. The Python AFC logic (stream → detect tool_calls → execute → continue) passes unit tests with a mock core, indicating a Rust-side issue in the real streaming path.

Normal (non-streaming) tool calling via OpenAI works fine using the example `examples/example_tool_calling.py`. This further suggests that only the streaming path with tools is affected.

## Environment

- Model: `openai/gpt-4o-mini`
- Provider: OpenAI
- Python examples:
  - `examples/example_openai_streaming.py` (works)
  - `examples/example_openai_streaming_tools.py` (hangs)
- Keys: `OPENAI_API_KEY` set (redacted in logs)
- OS: macOS (arm64)
- Timeout: 30s (Python client)

## Reproduction

1) Plain streaming (works)
```
python examples/example_openai_streaming.py
```
Observed:
- Non-streaming completion returned a joke
- Streaming prints “1, 2, 3, 4, 5.”

2) Streaming with tools (hangs)
```
python examples/example_openai_streaming_tools.py
```
Observed logs (abridged):
```
[dbg] provider=openai model=openai/gpt-4o-mini hybrid=0 timeout=30.0 key=OPENAI_API_KEY=sk-pro...DVAA
--- Streaming output start (OpenAI + tools) ---
Sending streaming request for openai
[bhumi] submit stream round=1 provider=openai model=gpt-4o-mini
[bhumi] tools_registered=True timeout=30.0
Worker 0: Received request
Worker 0: Active requests: 1
Worker 0: Got API key
... (no HTTP status, no SSE bytes) ...
# eventually Python timeout or KeyboardInterrupt
```

Also tried hybrid fallback (send second round non-streaming after tool_calls) via:
```
export BHUMI_HYBRID_TOOLS=1
python examples/example_openai_streaming_tools.py
```
Still hangs before any SSE chunk arrives.

## Expected vs Actual

- Expected: With tools present, first streaming round should emit `choices[].delta.tool_calls` chunks quickly, then finish_reason `tool_calls`. Client executes tool(s) and continues (streaming or hybrid). This matches our MockCore test.
- Actual: No SSE chunks are emitted at all when tools are present. The Rust worker prints “Got API key” but not the HTTP status; the request appears stuck before response consumption.

## Tests vs Reality

- `tests/test_streaming_tools.py` uses `MockCore` and passes (AFC flow validated in Python layer).
- Real provider path seems blocked in the Rust core when `tools` are included in the request.

Additional validation:
- `examples/example_tool_calling.py` (non-streaming tool use) works, confirming that tool registration and execution are correct in Python.
- `examples/example_openai_streaming.py` (streaming without tools) works.

## Hypotheses

- Rust core request/stream handling gets stuck when `tools` are present on OpenAI chat/completions:
  - Request never completes (server backpressure, handshake, or pending forever) due to missing/malformed fields.
  - Server returns non-success, but we don’t see it because the response body/status aren’t printed and no data is forwarded.
- Schema mismatch: Our tool schema includes `strict` flag; OpenAI may ignore it, but if rejected, should return 400 (would see status + body). Absence of status log suggests the `send().await` hasn’t completed.
- Header mismatch unlikely (plain streaming works). We forward the Authorization string as provided (Python adds `Bearer ...`).
- Core SSE parsing shouldn’t apply if we never get to bytes.

## Affected Code (Rust)

- File: `src/lib.rs`, worker loop around sending requests and handling responses:
  - URL selection for OpenAI: `"{base_url}/chat/completions"`
  - Headers construction from `_headers` Authorization
  - `.send().await` then handling of status and streaming branch
  - SSE parsing loop (`bytes_stream`, buffering, flushing on blank lines)

## Suggested Diagnostics (Rust)

Add temporary debug prints and guards in `src/lib.rs`:

- Before POST:
  - `println!("Worker {id}: POST {url} provider={provider} stream={bool} tools={bool}")`
- After response:
  - Log HTTP status (already present)
  - On non-success, log first 500 chars of body and push `[DONE]`
- In streaming branch:
  - Log `bytes.len()` for each `bytes_stream` frame
  - Log SSE event flushes: anthopic event type or generic OpenAI `data:` line lengths
  - Log final: saw `[DONE]` or forced
- Optional: wrap `.send().await` in `tokio::time::timeout(Duration::from_secs(30), ...)` for `stream=true` to catch handshake stalls and log accordingly

These will show if the request is stuck pre-response, returning non-success, or returning but not streaming.

## Workarounds

- Hybrid fallback (Python): After tool calls, switch second round to non-streaming. Note: In current state, we hang before even receiving first tool_call delta, so hybrid may not help.
- Non-tools streaming works as expected.

## Next Steps (Action Plan)

1) Add Rust debug instrumentation (owner: core)
   - Print POST metadata: URL, provider, `stream` flag, `tools` present.
   - After response: print HTTP status; on non-success, print first 500 chars of body and push `[DONE]` to queue.
   - In stream branch: log `bytes.len()` per frame and when flushing SSE events (Anthropic event name or OpenAI `data:` line), plus final `[DONE]` vs forced.

2) Add guarded timeout around initial send (owner: core)
   - Wrap `client.post(...).send().await` in `tokio::time::timeout` when `stream=true` (e.g., 30s).
   - On timeout, push an error JSON into the stream queue and `[DONE]` so Python surfaces fast.

3) Validate payload shape with tools (owner: python/core)
   - Log (debug) a sanitized preview of the outbound JSON (exclude `_headers`) when `tools` present.
   - Compare against OpenAI tool schema expectations; if needed, temporarily drop `strict` or simplify schema for a probe request.

4) Toggle HTTP mode diagnostic (owner: core)
   - Add env flag `BHUMI_HTTP1_ONLY=1` to build reqwest client with `http1_only(true)` to eliminate HTTP/2 streaming edge cases during debugging.

5) Reproduce and collect traces (owner: reporter)
   - Set `RUST_BACKTRACE=1` and run `examples/example_openai_streaming_tools.py`.
   - Capture new worker logs: POST banner, HTTP status, stream byte counts, SSE flushes.

6) Fix root cause (owner: core)
   - If non-success: adjust tool payload (schema/flags) until provider accepts and emits `tool_calls` deltas.
   - If stuck pre-response: investigate TLS/HTTP2, header formatting, or request body serialization.
   - If stream parsing: ensure SSE pass-through handles OpenAI `data:` lines with tool_calls and finish_reason correctly.

7) Regression coverage (owner: test)
   - Add a Rust-side test (feature-guarded or with a stub server) to simulate an OpenAI-like tools stream (tool_calls round then content round).
   - Extend Python tests to assert hybrid fallback toggling behavior remains optional and default AFC works.

8) Acceptance criteria
   - `examples/example_openai_streaming_tools.py` reliably streams tool_calls then final content with `BHUMI_HYBRID_TOOLS=0`.
   - No timeouts/hangs; Rust worker logs show POST, HTTP status, stream bytes, and `[DONE]`.
   - Non-stream tool example and plain streaming remain unaffected.

## Related Files

- Python: `src/bhumi/base_client.py` (astream_completion AFC logic; working with MockCore)
- Python: `src/bhumi/tools.py` (tool definitions & execution)
- Tests: `tests/test_streaming_tools.py` (validates AFC flow with mock core)
- Examples: `examples/example_openai_streaming.py` (works), `examples/example_openai_streaming_tools.py` (hangs)

---
Please keep this issue open until we add Rust-side diagnostics and confirm the fix or a precise failure mode with OpenAI when `tools` are present.

## Appendix: AFC (Automatic Function Calling) in this codebase

What is AFC:
- AFC is a streaming pattern where function/tool calls are detected in the streamed deltas and executed automatically without switching to a separate non-streaming mode. The stream continues across multiple rounds: the first round yields tool call deltas, then after invoking tools, the client resubmits with the tool results appended and continues streaming the final assistant content.

Where AFC is implemented (Python):
- `src/bhumi/base_client.py` → method `astream_completion`.
  - For OpenAI-compatible providers, the code accumulates `choices[].delta.tool_calls` fragments, detects `finish_reason == "tool_calls"`, executes tools via `ToolRegistry`, appends tool messages to the conversation, then resubmits to continue streaming.
  - For Anthropic, the code handles `tool_use` events (`content_block_start`/`input_json_delta`) and, on `message_stop`, executes tools and resubmits with `tool_result` blocks.

Supporting components:
- `src/bhumi/tools.py` → `ToolRegistry` and `execute_tool` handle parsing arguments, alias normalization, and invoking the Python coroutine function.

Tests covering AFC behavior:
- `tests/test_streaming_tools.py` drives a two-round streaming flow using `MockCore`:
  1) First round emits `tool_calls` deltas and finishes with `finish_reason="tool_calls"`.
  2) Client executes the tool and resubmits.
  3) Second round streams the final assistant text. The test asserts the tool is invoked once and the streamed output contains the expected content.

Expected provider event flow (OpenAI-compatible):
1) Submit stream request with `tools` included.
2) Receive SSE data lines containing JSON with `choices[0].delta.tool_calls[...]`.
3) Receive a line where `choices[0].finish_reason == "tool_calls"`.
4) Client executes tool(s) and resubmits (streaming) with the augmented `messages`.
5) Receive streamed `choices[0].delta.content` until a final stop.

Current failure mode:
- Step (2) never happens against the real provider: no SSE data is observed after the worker logs "Got API key". This leads to a Python timeout. Non-streaming tool example and non-tools streaming example both work, isolating the problem to streaming+tools in the Rust core path.
