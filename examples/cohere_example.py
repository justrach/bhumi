#!/usr/bin/env python3
"""
Cohere Provider Example for Bhumi

Demonstrates using Cohere's command-a-03-2025 model through Bhumi's unified interface.
Cohere uses OpenAI-compatible v1 endpoints.
"""

import asyncio
import os
from bhumi import BaseLLMClient, LLMConfig

async def main():
    # Get API key from environment
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("❌ Error: COHERE_API_KEY environment variable not set")
        print("   Get your key from: https://dashboard.cohere.com/api-keys")
        return
    
    print("=" * 70)
    print("🔷 Cohere Provider Example")
    print("=" * 70)
    
    # Configure Bhumi for Cohere
    config = LLMConfig(
        api_key=api_key,
        model="cohere/command-a-03-2025",  # Latest Cohere model
        provider="cohere"
    )
    
    client = BaseLLMClient(config)
    
    # Example 1: Simple completion
    print("\n📝 Example 1: Simple Completion")
    print("-" * 70)
    
    response = await client.completion(
        messages=[
            {"role": "user", "content": "Write a haiku about recursion in programming."}
        ]
    )
    
    print(f"Response: {response['choices'][0]['message']['content']}")
    
    # Example 2: Streaming
    print("\n\n🌊 Example 2: Streaming Response")
    print("-" * 70)
    
    print("Streaming: ", end="", flush=True)
    async for chunk in await client.completion(
        messages=[
            {"role": "user", "content": "Explain what makes Cohere unique in 2 sentences."}
        ],
        stream=True
    ):
        print(chunk, end="", flush=True)
    print("\n")
    
    # Example 3: Multi-turn conversation
    print("\n💬 Example 3: Multi-turn Conversation")
    print("-" * 70)
    
    conversation = [
        {"role": "user", "content": "What is the capital of France?"},
    ]
    
    response = await client.completion(messages=conversation)
    assistant_msg = response['choices'][0]['message']['content']
    print(f"User: {conversation[0]['content']}")
    print(f"Assistant: {assistant_msg}")
    
    # Continue conversation
    conversation.append({"role": "assistant", "content": assistant_msg})
    conversation.append({"role": "user", "content": "What's a famous landmark there?"})
    
    response = await client.completion(messages=conversation)
    assistant_msg = response['choices'][0]['message']['content']
    print(f"User: {conversation[2]['content']}")
    print(f"Assistant: {assistant_msg}")
    
    # Example 4: Different models
    print("\n\n🎯 Example 4: Using Different Cohere Models")
    print("-" * 70)
    
    models = [
        "cohere/command-a-03-2025",  # Latest model
        "cohere/command-r-plus",     # Previous generation
        "cohere/command-r",          # Smaller, faster
    ]
    
    for model in models:
        try:
            config = LLMConfig(api_key=api_key, model=model)
            client = BaseLLMClient(config)
            
            response = await client.completion(
                messages=[{"role": "user", "content": "Say hello in one word"}],
                max_tokens=10
            )
            
            content = response['choices'][0]['message']['content']
            print(f"✅ {model}: {content}")
        except Exception as e:
            print(f"❌ {model}: {str(e)[:50]}")
    
    print("\n" + "=" * 70)
    print("✅ Cohere examples completed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
