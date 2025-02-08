from ..base_client import BaseLLMClient, LLMConfig
from typing import Dict, Any, AsyncIterator, List
import json
import asyncio

class AnthropicLLM:
    """Anthropic implementation using BaseLLMClient"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        if not config.base_url:
            config.base_url = "https://api.anthropic.com/v1/messages"  # Use messages endpoint
        self.client = BaseLLMClient(config)
        
    async def completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Any:
        # Extract actual model name if it contains provider prefix
        model = self.config.model.split('/')[-1] if '/' in self.config.model else self.config.model
        
        request = {
            "_headers": {
                "x-api-key": self.config.api_key,
                "anthropic-version": self.config.api_version or "2023-06-01",
                "content-type": "application/json"
            },
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.pop("max_tokens", 1024),
            "stream": stream,
            **kwargs
        }
        
        if self.config.debug:
            print(f"Sending Anthropic request: {json.dumps(request, indent=2)}")
        
        if stream:
            return self._stream_completion(request)
        
        response = await self.client.completion(request)
        # Parse Anthropic's response format
        if isinstance(response, dict):
            try:
                if "content" in response:
                    return {
                        "text": response["content"][0]["text"],
                        "raw_response": response
                    }
                elif "error" in response:
                    return {
                        "text": f"Error: {response['error'].get('message', 'Unknown error')}",
                        "raw_response": response
                    }
            except Exception as e:
                if self.config.debug:
                    print(f"Error parsing response: {e}")
        return response
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Anthropic prompt format"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt += f"\n\nHuman: System instruction: {content}\n\nAssistant: I understand."
            elif role == "user":
                prompt += f"\n\nHuman: {content}"
            elif role == "assistant":
                prompt += f"\n\nAssistant: {content}"
        
        # Add final Human/Assistant marker for response
        if not prompt.endswith("Assistant:"):
            prompt += "\n\nAssistant:"
        
        return prompt.lstrip()
    
    async def _stream_completion(self, request: Dict[str, Any]) -> AsyncIterator[str]:
        """Handle streaming responses"""
        async for chunk in await self.client.completion(request, stream=True):
            try:
                if isinstance(chunk, str):
                    data = json.loads(chunk)
                    if "content" in data and data["content"]:
                        yield data["content"][0]["text"]
                    elif "error" in data:
                        yield f"Error: {data['error'].get('message', 'Unknown error')}"
                else:
                    yield chunk
            except:
                yield chunk 