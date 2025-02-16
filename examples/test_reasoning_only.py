import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
from dataclasses import dataclass
import os

# List of models that support reasoning
REASONING_MODELS = [
    "openai/o1-mini",
    "groq/deepseek-r1-distill-qwen-32b",
    "anthropic/claude-3-sonnet"  # Example, if it supports reasoning
]

@dataclass
class ReasoningResponse:
    """Special response class for reasoning models"""
    _reasoning: str
    _output: str
    _raw: dict
    
    @property
    def think(self) -> str:
        """Get the model's reasoning process"""
        return self._reasoning
    
    def __str__(self) -> str:
        """Default to showing just the output"""
        return self._output

async def main():
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model="groq/deepseek-r1-distill-qwen-32b",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    test_queries = [
        "What's the best way to learn programming?",
        "Compare Python and JavaScript for web development",
        "Explain how a car engine works in simple terms"
    ]
    
    for query in test_queries:
        print(f"\n\nQuery: {query}")
        try:
            response = await client.completion([
                {"role": "user", "content": query}
            ])
            
            # Check if response is a ReasoningResponse
            if hasattr(response, 'think'):
                print("\nReasoning:")
                print(response.think)
                print("\nResponse:")
                print(response)
            else:
                # Regular response
                print("\nResponse:")
                print(response["text"])
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(main()) 