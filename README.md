<p align="center">
  <img src="/assets/bhumi_logo.png" alt="Bhumi Logo" width="1600"/>
</p>


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/justrach/bhumi)

[![PyPI - Version](https://img.shields.io/pypi/v/bhumi.svg)](https://pypi.org/project/bhumi/)

# 🌍 **BHUMI v0.4.81 - The Fastest AI Inference Client** ⚡

## **Introduction**
Bhumi is the fastest AI inference client, built with Rust for Python. It is designed to maximize performance, efficiency, and scalability, making it the best choice for LLM API interactions. 

### **Why Bhumi?**
- 🚀 **Fastest AI inference client** – Outperforms alternatives with **2-3x higher throughput**
- ⚡ **Built with Rust for Python** – Achieves high efficiency with low overhead
- 🌐 **Supports 8+ AI providers** – OpenAI, Anthropic, Google Gemini, Groq, Cerebras, SambaNova, **Mistral**, and more
- 👁️ **Vision capabilities** – Image analysis across 5 providers (OpenAI, Anthropic, Gemini, Mistral, Cerebras)
- 🔄 **Streaming and async capabilities** – Real-time responses with Rust-powered concurrency
- 🔁 **Automatic connection pooling and retries** – Ensures reliability and efficiency
- 💡 **Minimal memory footprint** – Uses up to **60% less memory** than other clients
- 🏗 **Production-ready** – Optimized for high-throughput applications with OpenAI Responses API support

Bhumi (भूमि) is Sanskrit for **Earth**, symbolizing **stability, grounding, and speed**—just like our inference engine, which ensures rapid and stable performance. 🚀

## 🆕 **What's New in v0.4.81**

### ✨ **Major New Features**
- 🔍 **Dedicated OCR API**: Mistral's high-performance OCR with structured data extraction
- 📄 **Dual OCR Workflows**: Direct file upload + OCR or pre-uploaded file processing
- 🏗️ **Structured OCR**: Extract structured data with JSON schemas and bounding box analysis
- 📑 **Multi-page Processing**: Process specific pages or entire documents with high accuracy
- 🌐 **Multi-language OCR**: Support for 200+ languages including handwriting recognition

### 🛠 **Technical Improvements**
- **Enhanced OCR Integration**: `client.ocr()` and `client.upload_file()` methods
- **Unified API**: Single method handles both file upload and OCR processing
- **Better Error Handling**: Improved timeout and validation for OCR operations
- **Production Ready**: Optimized for high-volume document processing workflows

### 📊 **OCR Capabilities**
- **Document Types**: PDF, JPEG, PNG, and more formats
- **Text Extraction**: High-accuracy OCR with layout preservation
- **Structured Data**: Extract tables, forms, and key-value pairs
- **Bounding Boxes**: Precise text positioning and element detection
- **Multi-format Output**: Markdown text + structured JSON data

## 🆕 **What's New in v0.4.8**

### ✨ **Major New Features**
- 🌐 **8+ AI Providers**: Added **Mistral AI** support with vision capabilities (Pixtral models)
- 👁️ **Vision Support**: Image analysis across **5 providers** (OpenAI, Anthropic, Gemini, Mistral, Cerebras)
- 📡 **OpenAI Responses API**: Intelligent routing for new API patterns with better performance
- 🔧 **Satya v0.3.7**: Upgraded with nested model support and enhanced validation
- 🚀 **Production Ready**: Improved wheel building, Docker compatibility, and CI/CD

### 🛠 **Technical Improvements**
- **Cross-platform Wheels**: Enhanced building for Linux, macOS (Intel + Apple Silicon), Windows
- **OpenSSL Integration**: Proper SSL library linking for all platforms
- **Workflow Optimization**: Disabled integration tests for faster releases
- **Bug Fixes**: Resolved MAP-Elites buffer issues and Satya validation problems
- **Performance Optimizations**: Improved MAP-Elites archive loading with orjson + Satya validation
- **Production Ready**: Enhanced error handling and timeout protection

### 📊 **Provider Support Matrix**
| Provider | Chat | Streaming | Tools | Vision | Structured |
|----------|------|-----------|-------|---------|------------|
| OpenAI | ✅ | ✅ | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Gemini | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Groq | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| Cerebras | ✅ | ✅ | ✅* | ✅ | ⚠️ |
| SambaNova | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| OpenRouter | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| **Mistral** | ✅ | ✅ | ✅ | ✅ | ⚠️ |

*Cerebras tools require specific models

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

*Latest v0.4.8 release includes improved wheel building and cross-platform compatibility!*

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

### 🧠 **MAP-Elites Buffer Strategy (v0.4.8 Enhanced)**
- **Ultra-fast archive loading** with Satya v0.3.7 validation + orjson parsing (**3x faster** than standard JSON)
- **Trained buffer configurations** optimized through evolutionary algorithms  
- **Automatic buffer adjustment** based on response patterns and historical data
- **Type-safe validation** with comprehensive error checking
- **Secure loading** without unsafe `eval()` operations
- **Nested model support** for complex data structures

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

### 🏆 **Archive Distribution (v0.4.8 Enhanced)**
When you install Bhumi, you automatically get:
- Pre-trained MAP-Elites archive for optimal buffer sizing
- Fast orjson-based JSON parsing (2-3x faster than standard `json`)
- Satya v0.3.7-powered type validation for bulletproof data loading
- Performance metrics and diagnostics
- Nested model support for complex configurations

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

### Mistral AI Example (with Vision)
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

api_key = os.getenv("MISTRAL_API_KEY")

async def main():
    # Text-only model
    config = LLMConfig(
        api_key=api_key,
        model="mistral/mistral-small-latest",
        debug=True
    )
    
    client = BaseLLMClient(config)
    response = await client.completion([
        {"role": "user", "content": "Bonjour! Parlez-moi de Paris."}  # French language support
    ])
    print(f"Mistral Response: {response['text']}")

    # Vision model for image analysis
    vision_config = LLMConfig(
        api_key=api_key,
        model="mistral/pixtral-12b-2409"  # Pixtral vision model
    )
    
    vision_client = BaseLLMClient(vision_config)
    response = await vision_client.completion([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}}
            ]
        }
    ])
    print(f"Vision Analysis: {response['text']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Provider API: Multi-Provider Model Format

Bhumi unifies providers using a simple `provider/model` format in `LLMConfig.model`. Base URLs are auto-set for known providers; you can override with `base_url`.

- Supported providers: `openai`, `anthropic`, `gemini`, `groq`, `sambanova`, `openrouter`, `cerebras`, `mistral`
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

# Mistral AI
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-small-latest"))

# OpenRouter (gateway)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/meta-llama/llama-3.1-8b-instruct"))

# Mistral AI
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-small-latest"))

# Optional: override base URL
client = BaseLLMClient(LLMConfig(api_key="...", model="openai/gpt-4o", base_url="https://api.openai.com/v1"))
```

## 🎯 **Provider-Specific Model Access**

Bhumi supports accessing specialized models beyond the basic ones. Here's how to access different model variants and specialized capabilities:

### OpenAI Models
```python
# GPT-4 Family
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o"))              # Latest GPT-4 Optimized
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o-mini"))         # Fast GPT-4 variant
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4-turbo"))          # Turbo variant
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4"))                # Original GPT-4

# GPT-3.5 Family
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-3.5-turbo"))       # Latest Turbo

# Specialized Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4-vision-preview")) # Vision-capable GPT-4
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4-0125-preview"))   # Specific version

# Responses API (New) - Automatically uses Responses API
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o"))
response = await client.parse(input="Analyze this data", text_format=MyModel)  # Uses /responses endpoint
```

### Anthropic Models
```python
# Claude 3.5 Family
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-5-sonnet-latest"))  # Latest Sonnet
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-5-sonnet-20241022")) # Specific version

# Claude 3 Family
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-opus-latest"))       # Most capable
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-sonnet-20240229"))  # Balanced
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-3-haiku-20240307"))   # Fastest

# Claude 2 & Earlier
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-2.1"))                # Claude 2.1
client = BaseLLMClient(LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), model="anthropic/claude-instant-1.2"))        # Fast variant
```

### Google Gemini Models
```python
# Gemini 1.5 Family (Latest)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-1.5-pro-latest"))     # Most capable
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-1.5-flash-latest"))   # Fast variant
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-1.5-pro-001"))        # Specific version

# Gemini 1.0 Family
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-pro"))                # Text-only
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-pro-vision"))         # Vision-capable

# Experimental Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GEMINI_API_KEY"), model="gemini/gemini-exp-1114"))           # Experimental
```

### Mistral AI Models
```python
# Large Language Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-large-latest"))     # Most capable
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-medium-latest"))   # Balanced
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-small-latest"))    # Fast

# Code-Specific Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/codestral-latest"))         # Code generation
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/codestral-2405"))           # Specific version

# Vision Models (Pixtral)
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/pixtral-12b-2409"))         # Vision analysis
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/pixtral-large-latest"))     # Large vision model

### 🔍 **Mistral OCR & Document Analysis**
Mistral's Pixtral models excel at OCR (Optical Character Recognition) and document analysis, making them perfect for:
- **Text extraction** from images and documents
- **Document processing** (invoices, receipts, forms)
- **Handwriting recognition** 
- **Multilingual text extraction** (200+ languages)
- **Table and layout analysis**

```python
# OCR with Pixtral
vision_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("MISTRAL_API_KEY"), 
    model="mistral/pixtral-12b-2409"  # OCR specialist
))

# Extract text from receipt
receipt_response = await vision_client.completion([
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all text from this receipt:"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]
    }
])
print(f"OCR Result: {receipt_response['text']}")

# Analyze document layout
doc_response = await vision_client.completion([
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Analyze this document and extract key information:"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
    }
])
```

**OCR Capabilities:**
- **High accuracy** text extraction
- **Multi-language support** including handwriting
- **Table recognition** and structured data extraction  
- **Form processing** with field detection
- **Mathematical notation** recognition
- **Document classification** by type

## 🔍 **Dedicated OCR API (Mistral)**

Bhumi now supports Mistral's dedicated OCR API for high-performance document processing with structured data extraction:

### **Two OCR Workflows**

```python
# Workflow 1: Direct file upload + OCR (Recommended)
result = await client.ocr(
    file_path="/path/to/document.pdf",
    pages=[0, 1],  # Process specific pages
    model="mistral-ocr-latest"
)

# Workflow 2: Pre-uploaded file
upload_result = await client.upload_file("/path/to/document.pdf")
result = await client.ocr(
    document={"type": "file", "file_id": upload_result["id"]},
    pages=[0, 1]
)
```

### **OCR with Structured Output**

```python
# Define extraction schema
faq_schema = {
    "type": "text",
    "json_schema": {
        "name": "document_analysis",
        "description": "Extract key information from document",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "topics": {"type": "array", "items": {"type": "string"}},
                "key_points": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

# OCR with structured extraction
result = await client.ocr(
    file_path="/path/to/faq.pdf",
    pages=[0, 1],
    document_annotation_format=faq_schema,
    bbox_annotation_format=bbox_schema  # Optional: extract bounding boxes
)

# Access results
extracted_text = result["pages"][0]["markdown"]
structured_data = result["document_annotation"]
pages_processed = result["usage_info"]["pages_processed"]
```

### **OCR Features**

- **📄 Multi-format Support**: PDF, JPEG, PNG, and more
- **📑 Multi-page Processing**: Process specific pages or entire documents
- **🏗️ Structured Extraction**: Extract structured data with JSON schemas
- **📊 Bounding Box Analysis**: Get precise text positioning
- **🌐 Multi-language**: Support for 200+ languages
- **📈 High Performance**: Dedicated OCR models optimized for accuracy
- **🔄 Dual Workflows**: Direct upload or pre-uploaded file processing

### **OCR Response Format**

```python
{
    "pages": [
        {
            "index": 0,
            "markdown": "Extracted text content...",
            "images": [],
            "dimensions": {"dpi": 200, "height": 2200, "width": 1700}
        }
    ],
    "model": "mistral-ocr-2505-completion",
    "document_annotation": "Structured analysis...",
    "usage_info": {
        "pages_processed": 2,
        "doc_size_bytes": 1084515
    }
}
```

# Specialized Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mathstral-7b-v0.1"))        # Math specialist
client = BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/mistral-embed"))            # Embeddings
```

### Groq Models (Gateway)
```python
# Meta Llama Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama-3.1-405b-instruct"))      # Largest Llama
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama-3.1-70b-instruct"))       # 70B variant
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama-3.1-8b-instruct"))        # 8B variant

# Meta Llama 3 Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama3-70b-8192"))               # Llama 3 70B
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama3-8b-8192"))                # Llama 3 8B

# Other Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/mixtral-8x7b-32768"))            # Mixtral 8x7B
client = BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/gemma-7b-it"))                   # Google Gemma
```

### Cerebras Models (Gateway)
```python
# Llama Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("CEREBRAS_API_KEY"), model="cerebras/llama3.1-70b"))           # 70B model
client = BaseLLMClient(LLMConfig(api_key=os.getenv("CEREBRAS_API_KEY"), model="cerebras/llama3.1-8b"))            # 8B model

# Specialized Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("CEREBRAS_API_KEY"), model="cerebras/llama3.1-8b-instruct"))   # Instruction-tuned
```

### SambaNova Models (Gateway)
```python
# Llama Models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("SAMBANOVA_API_KEY"), model="sambanova/Meta-Llama-3.1-405B-Instruct"))  # Largest
client = BaseLLMClient(LLMConfig(api_key=os.getenv("SAMBANOVA_API_KEY"), model="sambanova/Meta-Llama-3.1-70B-Instruct"))   # 70B
client = BaseLLMClient(LLMConfig(api_key=os.getenv("SAMBANOVA_API_KEY"), model="sambanova/Meta-Llama-3.1-8B-Instruct"))    # 8B

# E5 Embeddings
client = BaseLLMClient(LLMConfig(api_key=os.getenv("SAMBANOVA_API_KEY"), model="sambanova/e5-mistral-7b-instruct"))        # Embedding model
```

### OpenRouter Models (Gateway)
```python
# Access any model via OpenRouter
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/meta-llama/llama-3.1-405b-instruct"))
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/anthropic/claude-3.5-sonnet"))
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/google/gemini-pro-1.5"))
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/mistralai/mistral-large"))

# Specialized models
client = BaseLLMClient(LLMConfig(api_key=os.getenv("OPENROUTER_API_KEY"), model="openrouter/anthropic/claude-3-haiku:beta")) # Beta models
```

## 🔍 **Provider Walkthroughs**

### OpenAI Walkthrough
```python
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig

async def openai_walkthrough():
    client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o",
        debug=True
    ))

    # 1. Basic Chat
    response = await client.completion([
        {"role": "user", "content": "Hello!"}
    ])
    print(f"Chat: {response['text']}")

    # 2. Vision Analysis
    vision_response = await client.completion([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
            ]
        }
    ])
    print(f"Vision: {vision_response['text']}")

    # 3. Structured Output (Responses API)
    from satya import Model, Field
    class Person(Model):
        name: str
        age: int

    parsed = await client.parse(
        input="Create a person named Alice, age 30",
        text_format=Person
    )
    print(f"Parsed: {parsed.parsed.name}, {parsed.parsed.age}")

    # 4. Streaming
    async for chunk in await client.completion([
        {"role": "user", "content": "Write a short story"}
    ], stream=True):
        print(chunk, end="", flush=True)

asyncio.run(openai_walkthrough())
```

### Mistral AI Walkthrough
```python
async def mistral_walkthrough():
    # Text Model
    text_client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("MISTRAL_API_KEY"),
        model="mistral/mistral-small-latest"
    ))

    # French language support
    response = await text_client.completion([
        {"role": "user", "content": "Bonjour! Comment allez-vous?"}
    ])
    print(f"French: {response['text']}")

    # Vision Model
    vision_client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("MISTRAL_API_KEY"),
        model="mistral/pixtral-12b-2409"
    ))

    vision_response = await vision_client.completion([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image:"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }
    ])
    print(f"Vision Analysis: {vision_response['text']}")

asyncio.run(mistral_walkthrough())
```

### Anthropic Walkthrough
```python
async def anthropic_walkthrough():
    client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="anthropic/claude-3-5-sonnet-latest"
    ))

    # Long context and reasoning
    response = await client.completion([
        {
            "role": "user",
            "content": "Analyze this complex problem and provide a detailed solution..."
        }
    ], max_tokens=4000)
    print(f"Analysis: {response['text']}")

    # Tool use
    def calculate(x: int, y: int) -> int:
        return x + y

    client.register_tool("calculate", calculate, "Add two numbers", {
        "type": "object",
        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        "required": ["x", "y"]
    })

    tool_response = await client.completion([
        {"role": "user", "content": "What is 15 + 27?"}
    ])
    print(f"Tool result: {tool_response['text']}")

asyncio.run(anthropic_walkthrough())
```

## 🛠 **Advanced Model Selection**

### Choosing the Right Model
```python
# For Speed (Fast inference, lower cost)
fast_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="openai/gpt-4o-mini"  # Fast variant
))

# For Quality (Best capabilities, higher cost)
quality_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="openai/gpt-4o"  # Most capable
))

# For Vision Tasks
vision_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral/pixtral-12b-2409"  # Specialized vision model
))

# For Code Generation
code_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral/codestral-latest"  # Code specialist
))

# For Math/Reasoning
math_client = BaseLLMClient(LLMConfig(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral/mathstral-7b-v0.1"  # Math specialist
))
```

### Model Switching at Runtime
```python
from bhumi.base_client import BaseLLMClient, LLMConfig

class MultiModelClient:
    def __init__(self):
        self.clients = {
            'fast': BaseLLMClient(LLMConfig(api_key=os.getenv("GROQ_API_KEY"), model="groq/llama-3.1-8b-instruct")),
            'quality': BaseLLMClient(LLMConfig(api_key=os.getenv("OPENAI_API_KEY"), model="openai/gpt-4o")),
            'vision': BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/pixtral-12b-2409")),
            'code': BaseLLMClient(LLMConfig(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral/codestral-latest"))
        }

    async def query(self, task_type: str, prompt: str):
        client = self.clients.get(task_type, self.clients['fast'])
        response = await client.completion([{"role": "user", "content": prompt}])
        return response['text']

# Usage
multi_client = MultiModelClient()

# Fast response
fast_answer = await multi_client.query('fast', 'Quick question?')

# High-quality response
quality_answer = await multi_client.query('quality', 'Complex analysis needed')

# Vision task
vision_answer = await multi_client.query('vision', 'Analyze this image...')

# Code generation
code_answer = await multi_client.query('code', 'Write a Python function...')
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

## 🚀 **Structured Outputs with Satya v0.3.7 High-Performance Validation**

Bhumi uses Satya v0.3.7 for structured outputs, providing **2-7x faster** validation than alternatives with OpenAI Responses API compatibility.

### Satya v0.3.7 Integration
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

### OpenAI Responses API Support
```python
# New Responses API patterns with intelligent routing
# OpenAI automatically uses Responses API when input= or instructions= provided

# Pattern 1: Simple input
completion = await client.parse(
    input="Create a user profile for Bob, age 30",
    text_format=UserProfile
)

# Pattern 2: Separated instructions
completion = await client.parse(
    instructions="Create a detailed user profile",
    input="Name: Sarah, Age: 28, Email: sarah@example.com",
    text_format=UserProfile
)

# Pattern 3: Streaming with Responses API
async for chunk in await client.parse(
    input="Write a story about AI",
    text_format=StoryModel,
    stream=True
):
    print(chunk.delta, end="", flush=True)
```

### Key Features
- **Satya v0.3.7**: Built-in OpenAI-compatible schema generation with nested model support
- **2-7x Performance**: Faster than alternative validation libraries
- **RFC 5322 Email Validation**: Proper email format checking
- **Decimal Precision**: Financial-grade number handling
- **Timeout Protection**: Built-in timeout with helpful error messages
- **Batch Processing**: `validator.set_batch_size(1000)` for high throughput
- **OpenAI Responses API**: Support for new API patterns with intelligent routing
- **Cross-Provider Compatibility**: Works with all supported providers
- **Built-in Tools**: Function calling with automatic tool execution

### Advanced Features
```python
from typing import List, Literal
from satya import Model, Field

# Nested models with complex validation
class CompanyProfile(Model):
    name: str = Field(description="Company name")
    employees: List[UserProfile] = Field(description="Employee profiles")
    founded_year: int = Field(description="Founding year", ge=1800, le=2025)

# Tool integration with structured outputs
class WeatherQuery(Model):
    location: str = Field(description="City name")
    unit: Literal["celsius", "fahrenheit"] = Field(description="Temperature unit")

def get_weather(query: WeatherQuery) -> dict:
    # Function automatically receives validated WeatherQuery object
    return {
        "location": query.location,
        "unit": query.unit,
        "temperature": 22,
        "forecast": "sunny"
    }

# Register tool and use with structured inputs
client.register_tool("get_weather", get_weather, "Get weather information", WeatherQuery)
```

### Performance Benefits
- **Satya v0.3.7**: 2-7x faster validation, RFC 5322 email validation, Decimal support, nested models
- **Production Optimized**: Built for high-throughput workloads requiring maximum performance
- **Memory Efficient**: Lower memory usage compared to alternatives
- **Type Safety**: Complete validation coverage with comprehensive error handling

### Provider Support for Structured Outputs
| Provider | Satya Support | Responses API |
|----------|---------------|---------------|
| OpenAI | ✅ | ✅ |
| Anthropic | ⚠️ | ❌ |
| Gemini | ⚠️ | ❌ |
| Groq | ⚠️ | ❌ |
| Cerebras | ⚠️ | ❌ |
| SambaNova | ⚠️ | ❌ |
| Mistral | ⚠️ | ❌ |

*OpenAI has full support for all structured output patterns. Other providers use prompt engineering with Satya validation.*

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



