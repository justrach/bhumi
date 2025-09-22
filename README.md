<p align="center">
  <img src="/assets/bhumi_logo.png" alt="Bhumi Logo" width="1600"/>
</p>


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/justrach/bhumi)

[![PyPI - Version](https://img.shields.io/pypi/v/bhumi.svg)](https://pypi.org/project/bhumi/)

# 🌍 **BHUMI - The Fastest AI Inference Client** ⚡

## **Introduction**
Bhumi is the fastest AI inference client, built with Rust for Python. It is designed to maximize performance, efficiency, and scalability, making it the best choice for LLM API interactions. 

### **Why Bhumi?**
- 🚀 **Fastest AI inference client** – Outperforms alternatives with **2-3x higher throughput**
- ⚡ **Built with Rust for Python** – Achieves high efficiency with low overhead
- 🌐 **Supports multiple AI providers** – OpenAI, Anthropic, Google Gemini, Groq, Cerebras, SambaNova, and more
- 🔄 **Streaming and async capabilities** – Real-time responses with Rust-powered concurrency
- 🔁 **Automatic connection pooling and retries** – Ensures reliability and efficiency
- 💡 **Minimal memory footprint** – Uses up to **60% less memory** than other clients
- 🏗 **Production-ready** – Optimized for high-throughput applications

Bhumi (भूमि) is Sanskrit for **Earth**, symbolizing **stability, grounding, and speed**—just like our inference engine, which ensures rapid and stable performance. 🚀

## Installation

**No Rust compiler required!** 🎊 Pre-compiled wheels are available for all major platforms:

```bash
pip install bhumi
```

**Supported Platforms:**
- 🐧 Linux (x86_64) 
- 🍎 macOS (Intel & Apple Silicon)
- 🪟 Windows (x86_64)
- 🐍 Python 3.8, 3.9, 3.10, 3.11, 3.12

*Previous versions required Rust installation. Now it's just one command!*

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

## ⚡ **Performance Optimizations**

Bhumi includes cutting-edge performance optimizations that make it **2-3x faster** than alternatives:

### 🧠 **MAP-Elites Buffer Strategy**
- **Ultra-fast archive loading** with Satya validation + orjson parsing (**3x faster** than standard JSON)
- **Trained buffer configurations** optimized through evolutionary algorithms  
- **Automatic buffer adjustment** based on response patterns and historical data
- **Type-safe validation** with comprehensive error checking
- **Secure loading** without unsafe `eval()` operations

### 📊 **Performance Status Check**
Check if you have optimal performance with the built-in diagnostics:

```python
from bhumi.utils import print_performance_status

# Check optimization status
print_performance_status()
# 🚀 Bhumi Performance Status
# ✅ Optimized MAP-Elites archive loaded  
# ⚡ Optimization Details:
#    • Entries: 15,644 total, 15,644 optimized
#    • Coverage: 100.0% of search space
#    • Loading: Satya validation + orjson parsing (3x faster)
```

### 🏆 **Archive Distribution**
When you install Bhumi, you automatically get:
- Pre-trained MAP-Elites archive for optimal buffer sizing
- Fast orjson-based JSON parsing (2-3x faster than standard `json`)
- Satya-powered type validation for bulletproof data loading
- Performance metrics and diagnostics

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

### Cerebras Example
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("CEREBRAS_API_KEY")

async def main():
    config = LLMConfig(
        api_key=api_key,
        model="cerebras/llama3.1-8b",  # gateway-style model parsing is supported
        debug=True,
    )

    client = BaseLLMClient(config)

    response = await client.completion([
        {"role": "user", "content": "Summarize the benefits of Bhumi in one sentence."}
    ])
    print(f"Response: {response['text']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Provider API: Multi-Provider Model Format

Bhumi unifies providers using a simple `provider/model` format in `LLMConfig.model`. Base URLs are auto-set for known providers; you can override with `base_url`.

- Supported providers: `openai`, `anthropic`, `gemini`, `groq`, `sambanova`, `openrouter`, `cerebras`
- Foundation providers use `provider/model`. Gateways like Groq/OpenRouter/SambaNova may use nested paths after the provider (e.g., `openrouter/meta-llama/llama-3.1-8b-instruct`).

```python
from bhumi.base_client import BaseLLMClient, LLMConfig

# OpenAI
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o"))

# Anthropic
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-5-sonnet-latest"))

# Gemini (OpenAI-compatible endpoint)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-2.0-flash"))

# Groq (gateway) – nested path after provider is kept intact
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama-3.1-8b-instant"))

# Cerebras (gateway)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("CEREBRAS_API_KEY"), model="cerebras/llama3.1-8b", base_url="https://api.cerebras.ai/v1"))

# SambaNova (gateway)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("SAMBANOVA_API_KEY"), model="sambanova/Meta-Llama-3.1-405B-Instruct"))

# OpenRouter (gateway)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/meta-llama/llama-3.1-8b-instruct"))

# Optional: override base URL
client = BaseLLMClient(LLMConfig(api_key="...", model="openai/gpt-4o", base_url="https://api.openai.com/v1"))
```

## Tool Use (Function Calling)

Bhumi supports OpenAI-style function calling and Gemini function declarations. Register Python callables with JSON schemas; Bhumi will add them to requests and execute tool calls automatically.

```python
import os, asyncio, json
from bhumi.base_client import BaseLLMClient, LLMConfig

# 1) Define a tool
def get_weather(location: str, unit: str = "celsius"):
    return {"location": location, "unit": unit, "forecast": "sunny", "temp": 27}

tool_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string", "description": "City and country"},
        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
}

async def main():
    client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o", debug=True))
    client.register_tool("get_weather", get_weather, "Get the current weather", tool_schema)

    # 2) Ask a question that should trigger a tool call
    resp = await client.completion([
        {"role": "user", "content": "What's the weather in Tokyo in celsius?"}
    ])

    print(resp["text"])  # Tool is executed and response incorporates tool output

asyncio.run(main())
```

Notes:

- OpenAI-compatible providers use `tools` with `tool_calls` in responses; Gemini uses `function_declarations` and `tool_config` under the hood.
- Bhumi parses tool calls, executes your Python function, appends a `tool` message, and continues the conversation automatically.

## 🚀 **Structured Outputs with High-Performance Validation**

Bhumi now supports structured outputs with both Pydantic and Satya validation, featuring the latest Satya v0.3.6 integration for **2-7x faster** validation:

### Satya v0.3.6 Integration (Recommended)
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
from satya import Model, Field

class UserProfile(Model):
    """High-performance user profile with Satya validation"""
    name: str = Field(description="User's full name")
    age: int = Field(description="User's age", ge=13, le=120)
    email: str = Field(description="Email address", email=True)  # RFC 5322 validation

async def main():
    client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o"))

    # Use parse() method similar to OpenAI's client.chat.completions.parse()
    completion = await client.parse(
        messages=[{"role": "user", "content": "Create user Alice, age 25"}],
        response_format=UserProfile,  # Satya model for high performance
        timeout=15.0  # Built-in timeout protection
    )

    user = completion.parsed  # Already validated with 2-7x performance boost!
    print(f"User: {user.name}, Age: {user.age}, Email: {user.email}")

asyncio.run(main())
```

### Key Features
- **Satya v0.3.6**: Built-in OpenAI-compatible schema generation
- **2-7x Performance**: Faster than Pydantic validation
- **RFC 5322 Email Validation**: Proper email format checking
- **Decimal Precision**: Financial-grade number handling
- **Timeout Protection**: Built-in timeout with helpful error messages
- **Batch Processing**: `validator.set_batch_size(1000)` for high throughput

### Pydantic Support (Standard)
```python
from pydantic import BaseModel
from bhumi.base_client import BaseLLMClient, LLMConfig

class UserProfile(BaseModel):
    name: str
    age: int
    email: str

# Same API works with Pydantic models too
completion = await client.parse(
    messages=[{"role": "user", "content": "Create user Bob, age 30"}],
    response_format=UserProfile
)
```

### Performance Comparison
- **Satya v0.3.6**: 2-7x faster validation, RFC 5322 email validation, Decimal support
- **Pydantic**: Rich ecosystem, comprehensive type coercion, excellent documentation
- **Use Satya** for production workloads requiring maximum performance
- **Use Pydantic** for development and complex validation scenarios

Learn more in our [Structured Outputs Documentation](STRUCTURED_OUTPUTS.md).

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

