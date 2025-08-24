import json
import pytest
import sys
from pathlib import Path

# Ensure local workspace package is used (prepend to take precedence over site-packages)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bhumi.utils import extract_json_from_text, parse_json_loosely


def test_extract_json_from_text_direct():
    data = extract_json_from_text('{"a": 1, "b": [1,2]}')
    assert data == {"a": 1, "b": [1, 2]}


def test_extract_json_from_text_fenced_block():
    text = """
    here you go:
    ```json
    {"x": 10, "y": [3,4,5]}
    ```
    thanks
    """
    data = extract_json_from_text(text)
    assert data == {"x": 10, "y": [3, 4, 5]}


def test_extract_json_from_text_balanced_object():
    text = "prefix {\n  \"k\": \"v\"\n} suffix"
    data = extract_json_from_text(text)
    assert data == {"k": "v"}


def test_parse_json_loosely_returns_default_on_failure():
    text = "no json here"
    data = parse_json_loosely(text, default={})
    assert data == {}


def test_parse_json_loosely_with_array():
    text = "-- [1, 2, 3] --"
    data = parse_json_loosely(text)
    assert data == [1, 2, 3]
