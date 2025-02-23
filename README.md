<p align="center">
  <img src="/assets/bhumi_logo.png" alt="Bhumi Logo" width="1600"/>
</p>

<h1 align="center"><b>Bhumi (भूमि)</b></h1>

# 🌍 **BHUMI - AI Client Setup and Usage Guide** ⚡

## **Introduction**
Bhumi (भूमि) is the Sanskrit word for **Earth**, symbolizing **stability, grounding, and speed**. Just as the Earth moves with unwavering momentum, **Bhumi AI ensures that your inference speed is as fast as nature itself!** 🚀 

A fast, async Python client for LLM APIs with Rust under the hood.

## Features
- Async support with Rust-powered concurrency
- Connection pooling and retry logic
- Streaming support
- Support for multiple providers:
  - OpenAI
  - Anthropic
  - Google Gemini
  - Groq
  - SambaNova

## Installation
```bash
pip install bhumi
```

## Quick Start

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

### Groq Example
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("GROQ_API_KEY")

async def main():
    config = LLMConfig(
        api_key=api_key,
        model="groq/llama-3.1-8b-it",
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

### SambaNova Example
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("SAMBANOVA_API_KEY")

async def main():
    config = LLMConfig(
        api_key=api_key,
        model="sambanova/Meta-Llama-3.3-70B-Instruct",
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

These benchmarks demonstrate Bhumi's superior performance, particularly in throughput where it outperforms other solutions by up to 3.2x.

## Configuration Options
The LLMConfig class supports various options:
- `api_key`: API key for the provider
- `model`: Model name in format "provider/model_name"
- `base_url`: Optional custom base URL
- `max_retries`: Number of retries (default: 3)
- `timeout`: Request timeout in seconds (default: 30)
- `max_tokens`: Maximum tokens in response
- `debug`: Enable debug logging

## 🎯 **Why Use Bhumi?**
✔ **Open Source:** Apache 2.0 licensed, free for commercial use  
✔ **Community Driven:** Welcomes contributions from individuals and companies  
✔ **Blazing Fast:** **2-3x faster** than alternative solutions  
✔ **Resource Efficient:** Uses **60% less memory** than comparable clients  
✔ **Multi-Model Support:** Easily switch between providers  
✔ **Parallel Requests:** Handles **multiple concurrent requests** effortlessly  
✔ **Flexibility:** Debugging and customization options available  
✔ **Production Ready:** Battle-tested in high-throughput environments

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