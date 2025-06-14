#!/usr/bin/env python3
"""
Test script for the OpenAI-compatible Gemini client
"""
import asyncio
import os
from src.bhumi.base import LLMConfig, create_llm

async def test_gemini_openai_compatible():
    """Test the Gemini client with OpenAI-compatible endpoint"""
    
    # You'll need to set your Gemini API key
    api_key = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
    
    if api_key == "your-gemini-api-key-here":
        print("Please set your GEMINI_API_KEY environment variable")
        return
    
    # Create configuration for Gemini with OpenAI-compatible endpoint
    config = LLMConfig(
        api_key=api_key,
        model="gemini/gemini-2.0-flash",  # This will be processed to use "gemini-2.0-flash"
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    # Create the LLM client
    llm = create_llm(config)
    print(f"Created client with base_url: {config.base_url}")
    print(f"Model: {config.model}")
    print(f"Provider: {config.provider}")
    
    # Test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain to me how AI works in one short paragraph."}
    ]
    
    try:
        print("\n=== Testing non-streaming completion ===")
        response = await llm.completion(messages)
        print("Response:", response.get("text", "No text found"))
        
        print("\n=== Testing streaming completion ===")
        stream = await llm.completion(messages, stream=True)
        print("Streaming response: ", end="")
        async for chunk in stream:
            print(chunk, end="", flush=True)
        print("\n")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_openai_compatible())
