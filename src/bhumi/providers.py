from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class BaseLLMConfig:
    api_base: str
    api_key_header: str
    model_path: str
    stream_marker: str
    stream_field_path: List[str]
    content_field_path: List[str]
    extra_headers: Optional[Dict[str, str]] = None

class SambanovaLLM:
    def __init__(self):
        self.config = BaseLLMConfig(
            api_base="https://api.sambanova.ai",
            api_key_header="Authorization: Bearer",
            model_path="/v1/chat/completions",
            stream_marker="data: [DONE]",
            stream_field_path=["choices", "0", "delta", "content"],
            content_field_path=["choices", "0", "message", "content"],
            extra_headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )

    def prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        """Convert messages to Sambanova format"""
        return {
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "model": kwargs.get("model", "sambanova-1"),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }

class GroqLLM:
    def __init__(self):
        self.config = BaseLLMConfig(
            api_base="https://api.groq.com",
            api_key_header="Authorization: Bearer",
            model_path="/v1/chat/completions",
            stream_marker="data: [DONE]",
            stream_field_path=["choices", "0", "delta", "content"],
            content_field_path=["choices", "0", "message", "content"],
            extra_headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Groq-Version": "2024-03-01"
            }
        )
    
    def prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        """Convert messages to Groq format"""
        return {
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "model": kwargs.get("model", "mixtral-8x7b-32768"),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }

# Example of a custom provider
class CustomLLM:
    def __init__(self, api_base: str = "https://api.custom.ai"):
        self.config = BaseLLMConfig(
            api_base=api_base,  # Can be changed when instantiating
            api_key_header="Authorization: Bearer",
            model_path="/v1/chat/completions",
            stream_marker="data: [DONE]",
            stream_field_path=["choices", "0", "delta", "content"],
            content_field_path=["choices", "0", "message", "content"],
            extra_headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )

    def prepare_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        return {
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "model": kwargs.get("model", "custom-model"),
            "temperature": kwargs.get("temperature", 0.7)
        } 