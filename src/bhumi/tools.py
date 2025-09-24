# tools_bhumi.py
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Callable, Union, Tuple
import copy

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    type: str
    function: Dict[str, Any]
    # Internal metadata not exposed to the model
    _aliases: Optional[Dict[str, str]] = None
    _on_unknown: Optional[str] = None  # 'drop' | 'error' | 'allow'

    @classmethod
    def create_function(
        cls,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        strict: bool = True,
        aliases: Optional[Dict[str, str]] = None,
        on_unknown: str = "drop",
    ) -> "Tool":
        """
        Create a function tool definition compatible with OpenAI/JSON-schema style.

        - Respects provided 'required' list.
        - Defaults additionalProperties=False for object schemas unless explicitly set.
        - Does NOT auto-require all properties.
        - Stores optional alias mapping (not part of the public schema).
        """
        # Work on a shallow copy to avoid caller side-effects
        params = dict(parameters) if parameters is not None else {"type": "object", "properties": {}}

        if params.get("type") == "object":
            # Default to strict additionalProperties if not specified
            params.setdefault("additionalProperties", False)
            # Ensure 'properties' exists and is a dict
            props = params.get("properties")
            if not isinstance(props, dict):
                props = {}
                params["properties"] = props
            # Respect any provided 'required'; default to none
            req = params.get("required")
            if req is not None:
                # Ensure required keys actually exist in properties
                params["required"] = [k for k in req if k in props]
            # else: leave 'required' absent to indicate no required fields
        # else: for non-object schemas, do not mutate

        return cls(
            type="function",
            function={
                "name": name,
                "description": description,
                "parameters": params,
                "strict": strict,
            },
            _aliases=aliases or None,
            _on_unknown=on_unknown or "drop",
        )


@dataclass
class ToolCall:
    id: str
    type: str
    function: Dict[str, Any]


class ToolRegistry:
    """
    Registry to store and manage tools with minimal, predictable validation.

    Features:
    - Respects provided JSON schema 'required' list.
    - Defaults additionalProperties=False for object schemas unless overridden.
    - Optional alias mapping per tool (e.g., {'writeto': 'write_to'}).
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._definitions: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: Dict[str, Any],
        *,
        strict: bool = True,
        aliases: Optional[Dict[str, str]] = None,
        on_unknown: str = "drop",
    ) -> None:
        """Register a new tool with optional alias normalization."""
        self._tools[name] = func
        self._definitions[name] = Tool.create_function(
            name=name,
            description=description,
            parameters=parameters,
            strict=strict,
            aliases=aliases,
            on_unknown=on_unknown,
        )

    def get_tool(self, name: str) -> Optional[Callable[..., Any]]:
        return self._tools.get(name)

    def get_definitions(self) -> List[Dict[str, Any]]:
        """
        Return public tool definitions for the model (OpenAI-style).
        Alias for get_public_definitions for backward compatibility.
        """
        return self.get_public_definitions()

    def get_public_definitions(self) -> List[Dict[str, Any]]:
        """
        Return only the public tool schema the model should see.
        Internal metadata like aliases is not exposed.
        """
        out: List[Dict[str, Any]] = []
        for t in self._definitions.values():
            params = self._relax_schema(t.function["parameters"])  # Relax to avoid provider-side rejections
            out.append(
                {
                    "type": t.type,
                    "function": {
                        "name": t.function["name"],
                        "description": t.function["description"],
                        "parameters": params,
                    },
                }
            )
        return out

    # --- Provider-specific schema exports ---
    def get_openai_definitions(self) -> List[Dict[str, Any]]:
        """
        OpenAI-compatible tool definitions (alias of get_public_definitions).
        """
        return self.get_public_definitions()

    def get_cerebras_definitions(self) -> List[Dict[str, Any]]:
        """
        Cerebras-compatible tool definitions:
        [{ type: "function", function: { name, strict: true, description, parameters } }]
        """
        out: List[Dict[str, Any]] = []
        for t in self._definitions.values():
            # For Cerebras, don't relax the schema - keep it strict
            params = t.function["parameters"]  # Use original strict schema
            out.append(
                {
                    "type": t.type,
                    "function": {
                        "name": t.function["name"],
                        "description": t.function["description"],
                        "strict": True,  # Cerebras requires this
                        "parameters": params,
                    },
                }
            )
        return out

    def get_anthropic_definitions(self) -> List[Dict[str, Any]]:
        """
        Anthropic-compatible tool definitions:
        [{ type: "function", function: { name, description, parameters } }]
        """
        out: List[Dict[str, Any]] = []
        for t in self._definitions.values():
            # For Anthropic, use relaxed schema
            params = self._relax_schema(t.function["parameters"])
            out.append(
                {
                    "type": t.type,
                    "function": {
                        "name": t.function["name"],
                        "description": t.function["description"],
                        "parameters": params,
                    },
                }
            )
        return out

    def _relax_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow-cloned schema relaxed for public export.
        - For object schemas, force additionalProperties=True to prevent provider validation failures
        - Do not mutate the internal stored schema
        """
        try:
            if not isinstance(schema, dict):
                return copy.deepcopy(schema)
            clone = copy.deepcopy(schema)
            if clone.get("type") == "object":
                # Allow unknown keys in public schema; internal validator will drop/handle them
                clone["additionalProperties"] = True
            return clone
        except Exception:
            # Fallback to original if deepcopy fails
            return schema

    async def execute_tool(self, tool_call: ToolCall, debug: bool = False) -> Any:
        """
        Execute a tool call with:
        - JSON argument parsing
        - Alias normalization
        - Minimal schema validation (required + additionalProperties)
        """
        name = tool_call.function["name"]
        func = self.get_tool(name)
        if not func:
            raise ValueError(f"Tool {name} not found")

        raw_args = tool_call.function.get("arguments", {})
        if isinstance(raw_args, str):
            try:
                args: Dict[str, Any] = json.loads(raw_args) if raw_args.strip() else {}
            except json.JSONDecodeError:
                # Parameterless or plain string fallbacks
                args = {}
        elif isinstance(raw_args, dict):
            args = dict(raw_args)
        else:
            args = {}

        definition = self._definitions.get(name)
        schema = definition.function["parameters"] if definition else {"type": "object", "properties": {}}
        aliases = (definition._aliases or {}) if definition else {}

        # Alias normalization
        if aliases:
            for src, dst in aliases.items():
                if src in args and dst not in args:
                    args[dst] = args.pop(src)

        # Sanitize + minimal validation (drop/allow/error for unknowns, shallow type coercion)
        args = self._validate_args(
            schema,
            args,
            tool_name=name,
            on_unknown=(definition._on_unknown or "drop"),
            debug=debug,
        )

        if debug:
            logger.debug("Executing tool=%s args=%s", name, json.dumps(args, indent=2))

        # Call function (sync or async)
        if asyncio.iscoroutinefunction(func):
            return await func(**args)
        return func(**args)

    # --- Execution adapters for provider response shapes ---
    async def execute_openai(self, tool_call_obj: Dict[str, Any], debug: bool = False) -> Any:
        """
        Execute a tool call from OpenAI tool_calls item shape:
        {
          "id": "call_...",
          "type": "function",
          "function": {"name": "...", "arguments": "{...}"}
        }
        """
        tool_call = ToolCall(
            id=tool_call_obj.get("id", ""),
            type=tool_call_obj.get("type", "function"),
            function=tool_call_obj.get("function", {}),
        )
        return await self.execute_tool(tool_call, debug=debug)

    async def execute_anthropic(self, tool_use_block: Dict[str, Any], debug: bool = False) -> Any:
        """
        Execute a tool call from Anthropic tool_use content block shape:
        {
          "type": "tool_use",
          "id": "toolu_...",
          "name": "...",
          "input": { ... }
        }
        """
        name = tool_use_block.get("name")
        input_args = tool_use_block.get("input", {})
        tool_call = ToolCall(
            id=tool_use_block.get("id", ""),
            type="function",
            function={"name": name, "arguments": input_args},
        )
        return await self.execute_tool(tool_call, debug=debug)

    def _validate_args(
        self,
        schema: Dict[str, Any],
        args: Dict[str, Any],
        tool_name: str,
        *,
        on_unknown: str = "drop",
        debug: bool = False,
    ) -> Dict[str, Any]:
        """
        Minimal JSON-object validation + sanitization:
        - Enforce required presence
        - Unknown keys behavior per-tool: 'drop' (default), 'error', or 'allow'
        - Shallow type coercion for basic types (int/float/bool) from strings
        Returns sanitized args
        """
        if not isinstance(schema, dict) or schema.get("type") != "object":
            # Only validate object schemas
            return args

        props: Dict[str, Any] = schema.get("properties", {}) or {}
        required: List[str] = schema.get("required", []) or []
        additional: bool = schema.get("additionalProperties", False)

        allowed = set(props.keys())
        sanitized = dict(args)

        # Handle unknowns first
        unknown = [k for k in sanitized.keys() if k not in allowed]
        if unknown:
            if on_unknown == "error" and additional is False:
                raise ValueError(
                    f"Tool '{tool_name}' received unknown parameter(s): {', '.join(unknown)}; allowed: {', '.join(sorted(allowed))}"
                )
            if on_unknown == "drop":
                for k in unknown:
                    sanitized.pop(k, None)
                if debug and unknown:
                    logger.debug("Tool %s dropped unknown args: %s", tool_name, ", ".join(unknown))
            # if 'allow', keep as-is

        # Required presence after unknown handling
        missing = [k for k in required if k not in sanitized]
        if missing:
            raise ValueError(f"Tool '{tool_name}' missing required parameter(s): {', '.join(missing)}")

        # Shallow type coercion based on schema where possible
        for key, spec in props.items():
            if key not in sanitized:
                continue
            val = sanitized[key]
            t = (spec or {}).get("type")
            try:
                if t == "integer" and isinstance(val, str) and val.strip().isdigit():
                    sanitized[key] = int(val)
                elif t == "number" and isinstance(val, str):
                    sanitized[key] = float(val)
                elif t == "boolean" and isinstance(val, str):
                    low = val.lower().strip()
                    if low in {"true", "1", "yes", "y"}:
                        sanitized[key] = True
                    elif low in {"false", "0", "no", "n"}:
                        sanitized[key] = False
                elif t == "array" and isinstance(val, str) and val.strip().startswith("["):
                    sanitized[key] = json.loads(val)
            except Exception:
                # Keep original if coercion fails
                pass

        return sanitized