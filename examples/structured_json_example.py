#!/usr/bin/env python3
"""
Example: Robust JSON extraction and StructuredOutput usage.

This example shows how to parse loosely formatted model responses that contain
JSON in code fences or mixed text using Bhumi's utilities and StructuredOutput.
"""
import os
import json
from typing import List
from pydantic import BaseModel

from bhumi.base_client import StructuredOutput
from bhumi.utils import parse_json_loosely


class TodoItem(BaseModel):
    title: str
    done: bool = False

class TodoList(BaseModel):
    items: List[TodoItem]


def main():
    # Simulated messy LLM response containing JSON in a fenced block
    messy = """
    Sure! Here's the plan:

    ```json
    {
      "items": [
        {"title": "Write tests", "done": true},
        {"title": "Implement feature", "done": false}
      ]
    }
    ```

    Let me know if you'd like any changes.
    """

    print("Raw text:\n", messy)

    # Direct utility usage
    data = parse_json_loosely(messy, default={})
    print("\nParsed with parse_json_loosely():\n", json.dumps(data, indent=2))

    # StructuredOutput usage
    so = StructuredOutput(TodoList)
    model_obj = so.parse_response(messy)
    print("\nValidated Pydantic model:")
    print(model_obj)


if __name__ == "__main__":
    main()
