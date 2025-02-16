from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
import json
import asyncio

@dataclass
class ToolParameter:
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    properties: Optional[Dict[str, 'ToolParameter']] = None
    required: Optional[List[str]] = None
    items: Optional['ToolParameter'] = None
    additionalProperties: Optional[bool] = None

@dataclass
class Tool:
    type: str = "function"
    function: Dict[str, Any] = None
    
    @classmethod
    def create_function(
        cls,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        strict: bool = True
    ) -> 'Tool':
        """Create a function tool definition"""
        # Ensure additionalProperties is set to false
        if "type" in parameters and parameters["type"] == "object":
            parameters["additionalProperties"] = False
        
        # Ensure all properties are listed as required
        if "properties" in parameters:
            parameters["required"] = list(parameters["properties"].keys())
    
        return cls(
            type="function",
            function={
                "name": name,
                "description": description,
                "parameters": parameters,
                "strict": strict
            }
        )

@dataclass
class ToolCall:
    id: str
    type: str
    function: Dict[str, Any]

class ToolRegistry:
    """Registry to store and manage available tools"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, Tool] = {}
        
    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Register a new tool"""
        self._tools[name] = func
        self._definitions[name] = Tool.create_function(
            name=name,
            description=description,
            parameters=parameters
        )
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get the registered tool function"""
        return self._tools.get(name)
        
    def get_definitions(self) -> List[Tool]:
        """Get all tool definitions"""
        return list(self._definitions.values())
        
    async def execute_tool(self, tool_call: ToolCall, debug: bool = False) -> Any:
        """Execute a tool call and return the result"""
        if debug:
            print(f"\nExecuting tool: {tool_call.function['name']}")
        
        func = self.get_tool(tool_call.function["name"])
        if not func:
            raise ValueError(f"Tool {tool_call.function['name']} not found")
            
        # Handle different argument formats
        args = tool_call.function["arguments"]
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                # Gemini might return arguments as a plain string for parameterless functions
                args = {}
        
        if debug:
            print(f"Tool arguments: {json.dumps(args, indent=2)}")
        
        # Execute the tool
        if callable(func):
            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                result = func(**args)
            
            if debug:
                print(f"Tool result: {result}")
            
            return result
        
        raise ValueError(f"Invalid tool function: {func}") 