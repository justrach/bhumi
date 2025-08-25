"""Lightweight JSON compatibility layer.

Uses orjson if available for performance, otherwise falls back to stdlib json.

Functions:
- loads: parse JSON string -> Python object
- dumps: serialize Python object -> JSON string
- JSONDecodeError: exception type raised on parse errors
"""

from typing import Any

try:  # Prefer orjson for speed
    import orjson as _json  # type: ignore
    _USING_ORJSON = True
except Exception:  # Fallback to stdlib
    import json as _json  # type: ignore
    _USING_ORJSON = False


try:
    JSONDecodeError = _json.JSONDecodeError  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - extremely unlikely
    JSONDecodeError = ValueError  # type: ignore


def loads(s: str) -> Any:
    return _json.loads(s)


def dumps(obj: Any) -> str:
    # orjson.dumps returns bytes; stdlib returns str
    data = _json.dumps(obj)
    if _USING_ORJSON and isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8")
    return data  # type: ignore[return-value]

