# Only export the Python wrapper classes
from .client import (
    GeminiClient,
    AnthropicClient, 
    OpenAIClient,
    CompletionResponse
)

# Export base client for advanced usage
from .base_client import BaseLLMClient, LLMConfig, ReasoningResponse

# Export new structured outputs functionality
from .structured_outputs import (
    ResponseFormat,
    ParsedChatCompletion, 
    ParsedMessage,
    ParsedChoice,
    pydantic_function_tool,
    pydantic_tool_schema,
    create_openai_tools_from_models,
    create_anthropic_tools_from_models,
    parse_tool_call_arguments,
    StructuredOutputError,
    LengthFinishReasonError,
    ContentFilterFinishReasonError,
    SchemaValidationError
)

# Export utility functions for checking performance optimization  
from .utils import check_performance_optimization, print_performance_status

__all__ = [
    # Client classes
    'GeminiClient',
    'AnthropicClient',
    'OpenAIClient',
    'CompletionResponse',
    'BaseLLMClient',
    'LLMConfig',
    'ReasoningResponse',
    
    # Structured outputs
    'ResponseFormat',
    'ParsedChatCompletion',
    'ParsedMessage', 
    'ParsedChoice',
    'pydantic_function_tool',
    'pydantic_tool_schema',
    'create_openai_tools_from_models',
    'create_anthropic_tools_from_models',
    'parse_tool_call_arguments',
    'StructuredOutputError',
    'LengthFinishReasonError',
    'ContentFilterFinishReasonError',
    'SchemaValidationError',
    
    # Utilities
    'check_performance_optimization',
    'print_performance_status'
] 