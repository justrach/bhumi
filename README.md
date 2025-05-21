<p align="center">
  <img src="/assets/bhumi_logo.png" alt="Bhumi Logo" width="1600"/>
</p>

<h1 align="center"><b>Bhumi</b></h1>

# 🌍 **BHUMI - The Fastest AI Inference Client** ⚡

## **Introduction**
Bhumi is the fastest AI inference client, built with Rust for Python. It is designed to maximize performance, efficiency, and scalability, making it the best choice for LLM API interactions. 

### **Why Bhumi?**
- 🚀 **Fastest AI inference client** – Outperforms alternatives with **2-3x higher throughput**
- ⚡ **Built with Rust for Python** – Achieves high efficiency with low overhead
- 🌐 **Supports leading AI providers** – Including OpenAI, Anthropic, Google Gemini, Groq, and SambaNova.
- 🔄 **Streaming and async capabilities** – Real-time responses with Rust-powered concurrency
- 🔁 **Automatic connection pooling and retries** – Ensures reliability and efficiency
- 💡 **Minimal memory footprint** – Uses up to **60% less memory** than other clients
- 🏗 **Production-ready** – Optimized for high-throughput applications and battle-tested in high-throughput environments
- 🤝 **Parallel Requests** – Handles **multiple concurrent requests** effortlessly
- 🛠️ **Flexibility** – Debugging and customization options available
- 📜 **Open Source** – Apache 2.0 licensed, free for commercial use
- 🤗 **Community Driven** – Welcomes contributions from individuals and companies

Bhumi (भूमि) is Sanskrit for **Earth**, symbolizing **stability, grounding, and speed**—just like our inference engine, which ensures rapid and stable performance. 🚀

## Installation
```bash
pip install bhumi
```

## Quick Start

To get started, you'll primarily interact with two main components: `LLMConfig` and `BaseLLMClient`. `LLMConfig` is used to set up your client configuration, including API keys, model selection, and other parameters. `BaseLLMClient` is then instantiated with this configuration and serves as the main interface for making API calls like completions and streaming.

**Note:** The examples below assume you have set your API keys as environment variables (e.g., `OPENAI_API_KEY` for OpenAI, `GEMINI_API_KEY` for Gemini). The code uses `os.getenv()` to retrieve these keys.

### OpenAI Example
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("OPENAI_API_KEY")

async def main():
    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-4o",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"Response: {response['text']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Gemini Example
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("GEMINI_API_KEY")

async def main():
    config = LLMConfig(
        api_key=api_key,
        model="gemini/gemini-2.0-flash",
        debug=True
    )
    
    client = BaseLLMClient(config)
    
    response = await client.completion([
        {"role": "user", "content": "Tell me a joke"}
    ])
    print(f"Response: {response['text']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Streaming Support
All providers support streaming responses:

```python
async for chunk in await client.completion([
    {"role": "user", "content": "Write a story"}
], stream=True):
    print(chunk, end="", flush=True)
```

## 🛠️ Tool Calling Example
Bhumi supports tool calling, allowing the LLM to interact with external functions to get information or perform actions. Here's how you can set it up:

**Note:** This example uses OpenAI. Ensure your `OPENAI_API_KEY` environment variable is set.

```python
import asyncio
import os
import json
from bhumi.base_client import BaseLLMClient, LLMConfig

# 1. Define your asynchronous tool function
async def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Gets the current weather in a given location."""
    # In a real scenario, this would call a weather API
    print(f"Tool called: get_weather(location='{location}', unit='{unit}')")
    if "san francisco" in location.lower():
        return json.dumps({"temperature": "70", "unit": unit, "description": "Sunny"})
    return json.dumps({"temperature": "unknown", "unit": unit, "description": "Weather data not found"})

async def main():
    # 2. Set up LLMConfig and BaseLLMClient
    # Make sure OPENAI_API_KEY is set in your environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    config = LLMConfig(
        api_key=api_key,
        model="openai/gpt-4o-mini", # Or any model that supports tool calling
        # debug=True # Uncomment for detailed logs
    )
    client = BaseLLMClient(config)

    # 3. Register the tool with the client
    client.register_tool(
        name="get_weather",
        func=get_weather,
        description="Get the current weather for a specific location.",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g., San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit for temperature, either celsius or fahrenheit.",
                },
            },
            "required": ["location", "unit"],
        },
    )

    # 4. Make a completion call that might trigger the tool
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco in fahrenheit?"}
    ]
    
    print(f"\nUser query: {messages[0]['content']}")
    
    response = await client.completion(messages)
    
    # The response will contain the model's message, which incorporates the tool's output.
    # If a tool was called, Bhumi handles the multi-step conversation automatically.
    print(f"\nFinal LLM Response: {response.get('text')}")
    # Expected interaction:
    # 1. User asks about weather.
    # 2. LLM decides to call 'get_weather'.
    # 3. Bhumi executes 'get_weather("San Francisco", "fahrenheit")'.
    # 4. 'get_weather' returns '{"temperature": "70", "unit": "fahrenheit", "description": "Sunny"}'.
    # 5. Bhumi sends this tool output back to the LLM.
    # 6. LLM uses this information to generate the final response, e.g.,
    #    "The weather in San Francisco is 70°F and sunny."

if __name__ == "__main__":
    # To run this example, ensure you have python-dotenv installed (pip install python-dotenv)
    # and an .env file with your OPENAI_API_KEY, or set it as an environment variable.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("python-dotenv not found, please set OPENAI_API_KEY environment variable manually.")
        pass # Allow running if OPENAI_API_KEY is already set in environment

    asyncio.run(main())
```
This example demonstrates registering a `get_weather` tool and how Bhumi handles the interaction when the LLM decides to use it. The actual output will depend on the LLM's interpretation and the tool's response.

## 📊 **Benchmark Results**
Our latest benchmarks show significant performance advantages across different metrics:
![alt text](gemini_averaged_comparison_20250131_154711.png)

### ⚡ Response Time
- LiteLLM: 13.79s
- Native: 5.55s
- Bhumi: 4.26s
- Google GenAI: 6.76s

### 🚀 Throughput (Requests/Second)
- LiteLLM: 3.48
- Native: 8.65
- Bhumi: 11.27
- Google GenAI: 7.10

### 💾 Peak Memory Usage (MB)
- LiteLLM: 275.9MB
- Native: 279.6MB
- Bhumi: 284.3MB
- Google GenAI: 284.8MB

These benchmarks demonstrate Bhumi's superior performance, particularly in throughput where it can outperform other solutions significantly.

## Configuration Options
The `LLMConfig` class supports various options to customize the client's behavior:
- **`api_key`**: API key for the provider.
- **`model`**: Model name in the format "provider/model_name" (e.g., "openai/gpt-4o", "gemini/gemini-2.0-flash").
- **`base_url`**: Optional custom base URL for API requests. Useful for proxies or self-hosted models.
- **`max_retries`**: Number of automatic retries for failed requests (default: 3).
- **`timeout`**: Request timeout in seconds (default: 30).
- **`max_tokens`**: Maximum number of tokens to generate in the response.
- **`debug`**: Boolean flag to enable or disable debug logging (default: `False`).

## 🤝 **Contributing**
We welcome contributions from the community! Whether you're an individual developer or representing a company like Google, OpenAI, or Anthropic, feel free to:

- Submit pull requests
- Report issues
- Suggest improvements
- Share benchmarks
- Integrate our optimizations into your libraries (with attribution)

## 📜 **License**
Apache 2.0

🌟 **Join our community and help make AI inference faster for everyone!** 🌟

