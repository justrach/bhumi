from typing import Dict, List, Optional, AsyncGenerator, Union
from ..base_client import BaseLLMClient, LLMConfig

class SambanovaClient:
    """Client for SambaNova's API using OpenAI-compatible endpoints"""
    
    def __init__(self, config: LLMConfig, client: BaseLLMClient):
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.sambanova.ai/v1"
        self.model = config.model.replace("sambanova/", "")  # Remove sambanova/ prefix if present
        self.client = client
        
    async def completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        system_prompt: str = "You are a helpful assistant",
        **kwargs
    ) -> Union[dict, AsyncGenerator[str, None]]:
        """Send a completion request to SambaNova"""
        
        # Add system prompt if not present
        if not any(msg.get("role") == "system" for msg in messages):
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **({"max_tokens": self.client.config.max_tokens} if self.client.config.max_tokens else {}),
            **kwargs
        }
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )
        
        if stream:
            async for chunk in response.iter_lines():
                if chunk:
                    try:
                        if chunk.startswith('data: '):
                            chunk = chunk[6:]  # Remove 'data: ' prefix
                        if chunk and chunk != '[DONE]':
                            yield chunk
                    except Exception as e:
                        print(f"Error parsing chunk: {e}")
        else:
            response_json = await response.json()
            return {
                "text": response_json["choices"][0]["message"]["content"],
                "raw": response_json
            } 