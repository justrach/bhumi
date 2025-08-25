# ADR: Handling Streaming JSON Primitives in SSE (OpenAI-Compatible)

- Status: Accepted
- Date: 2025-08-25
- Owners: Bhumi runtime/LLM client

## Context

We observed inconsistent streaming behavior in the OpenAI example:

- Prompt “Write a haiku about AI” streamed correctly.
- Prompt “Count to 5” printed only punctuation (", , , , .") and dropped digits.

Root cause: our Python streamer (`BaseLLMClient.astream_completion`) assumed each streamed chunk, once `json.loads`-parsed, would be a dictionary with OpenAI-compatible shape (`{"choices": [{"delta": {"content": ...}}]}`). However, the Rust core can forward Server-Sent Event (SSE) chunks that are already-unwrapped JSON primitives (e.g., a single string token like "1" or ","). When `json.loads` returns a primitive (string/number), our code previously ignored it, causing digit-only tokens to be lost.

This explains why free-form text (haiku) worked — it arrived via dict `delta.content` — while simple numeric output did not.

## Decision

When a streamed chunk parses successfully as JSON but is not a dict, yield it directly as text.

Specifically, in `astream_completion` (file: `src/bhumi/base_client.py`), after `json.loads(chunk)`, if the parsed value is not a dict, convert it to `str` and `yield` it. This preserves primitive tokens (digits, commas, etc.).

## Rationale

- Minimal, provider-agnostic fix at the Python client boundary.
- Keeps existing handling for OpenAI-compatible dict deltas unchanged.
- Avoids larger changes in the Rust core or enforcing strict SSE framing everywhere.
- Backwards compatible for providers that already emit standard `choices/delta` structures.

## Alternatives Considered

- Normalize in Rust core so all chunks are wrapped in OpenAI-compatible dicts.
  - Heavier change, broader surface area, and couples core to one schema.
- Strict SSE parser with line buffering and schema enforcement in Python.
  - More complex and not necessary for this bug; risk of regressions.
- Accumulate only `delta.content` and drop everything else.
  - Reintroduces the original bug for primitive tokens.

## Implementation

File: `src/bhumi/base_client.py`

Change inside `astream_completion` streaming loop:

```
data = json.loads(chunk)

# If provider returns a JSON primitive (string/number), yield it directly
if not isinstance(data, dict):
    text = str(data)
    if text:
        yield text
    continue
```

All existing branches for Anthropic and OpenAI-compatible `choices/delta` remain intact. SSE fallback for raw `data: ...` lines is unchanged.

Performance improvement: introduced `src/bhumi/json_compat.py`, a thin shim that uses `orjson` when available and falls back to `json`. The client now imports `loads`/`dumps`/`JSONDecodeError` from this shim to accelerate hot paths (especially streaming) while keeping zero-setup compatibility.

## Consequences

- “Count to 5” now prints digits correctly: `1, 2, 3, 4, 5.`
- No change for haiku/text outputs (still handled via `delta.content`).
- Very low risk: only affects chunks that parse as JSON primitives (previously dropped). Dict-shaped chunks are unaffected.

## Testing

- Manual: run `examples/example_openai.py` with “Count to 5” and with the haiku prompt; verify both stream correctly.
- Suggested unit test: simulate the stream by feeding a sequence of primitive chunks (e.g., `"1"`, `","`, `"2"`, ...) and assert the yielded concatenation matches expected.

## Security & Privacy

- No changes to headers, auth, or logging of secrets.
- No additional data persisted.

## Compatibility

- Backwards compatible with OpenAI, Groq, OpenRouter, SambaNova, Gemini (OpenAI path), and Anthropic handling.

## Open Questions

- Do we want to enforce a stricter SSE framing contract in the Rust core to reduce client-side branching?
- Should we expose a pluggable parser strategy per provider for advanced users?

## References

- `examples/example_openai.py`
- `src/bhumi/base_client.py` (method: `astream_completion`)
