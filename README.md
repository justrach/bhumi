<p align="center">
  <img src="https://images.bhumi.trilok.ai/bhumi_logo.png" alt="Bhumi Logo" width="200"/>
</p>

<h1 align="center"><b>Bhumi (भूमि)</b></h1>

# 🌍 **BHUMI - AI Client Setup and Usage Guide** ⚡

## **Introduction**
Bhumi (भूमि) is the Sanskrit word for **Earth**, symbolizing **stability, grounding, and speed**. Just as the Earth moves with unwavering momentum, **Bhumi AI ensures that your inference speed is as fast as nature itself!** 🚀 

Bhumi is designed to **optimize and accelerate AI inference** while maintaining simplicity, flexibility, and multi-model support. Whether you're working with **OpenAI, Anthropic, or Gemini**, Bhumi makes switching between providers seamless.

---

## **1️⃣ Installation**
To install Bhumi, run the following commands:

```bash
rm -rf target/wheels/*
pip uninstall bhumi
maturin develop
```

> **Note:** Ensure you have **Rust** and **Python** installed before proceeding.

---

## **2️⃣ Environment Setup**
Before running Bhumi, set up your API keys in your terminal:

```bash
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

---

## **3️⃣ Python Usage**
Here's a basic example to get started with Bhumi:

```python
import os
from bhumi import Bhumi

# Get API keys
OPENAI_KEY = os.environ['OPENAI_API_KEY']
GEMINI_KEY = os.environ['GEMINI_API_KEY']
ANTHROPIC_KEY = os.environ['ANTHROPIC_API_KEY']

# Example prompt
prompt = "Explain what a neural network is in one sentence."

# OpenAI example
openai_client = Bhumi(
    max_concurrent=10,
    provider="openai",
    model="gpt-4o",
    debug=True
)
openai_response = openai_client.completion(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    api_key=OPENAI_KEY
)
print("
🌟 OpenAI Response:", openai_response.text)

# Gemini example
gemini_client = Bhumi(
    max_concurrent=10,
    provider="gemini",
    model="gemini-1.5-ultra",
    debug=True
)
gemini_response = gemini_client.completion(
    model="gemini/gemini-1.5-ultra",
    messages=[{"role": "user", "content": prompt}],
    api_key=GEMINI_KEY
)
print("
💡 Gemini Response:", gemini_response.text)

# Anthropic example
anthropic_client = Bhumi(
    max_concurrent=10,
    provider="anthropic",
    model="claude-3-opus",
    debug=True
)
anthropic_response = anthropic_client.completion(
    model="anthropic/claude-3-opus",
    messages=[{"role": "user", "content": prompt}],
    api_key=ANTHROPIC_KEY
)
print("
🤖 Anthropic Response:", anthropic_response.text)
```

---

## **4️⃣ Supported Models**
Bhumi supports **ALL models** from **OpenAI, Anthropic, and Gemini**, giving you full flexibility!

### 🔵 **OpenAI**
- `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`, and more!

### 🟠 **Anthropic**
- `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`, and more!

### 🟢 **Gemini**
- `gemini-1.5-ultra`, `gemini-1.5-pro`, `gemini-1.5-flash`, and more!

---

## ❌ **Current Limitations**
- 🚫 **No Tool Use:** Bhumi does not currently support function calling or tool use.
- 🚫 **No Streaming:** Responses are returned in a single batch; streaming is not yet available.

---

## 🎯 **Why Use Bhumi?**
✔ **Fast Inference:** Optimized for **speed and efficiency**  
✔ **Multi-Model Support:** Easily switch between **OpenAI, Anthropic, and Gemini**  
✔ **Parallel Requests:** Handles **multiple concurrent requests** effortlessly  
✔ **Flexibility:** Debugging and customization options available  

---

🚀 **Get started with Bhumi today and experience next-level AI inference!** 🚀
