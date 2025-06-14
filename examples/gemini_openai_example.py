#!/usr/bin/env python3
"""
Example showing how to use Gemini with OpenAI-compatible endpoint through Bhumi
This now uses direct HTTP requests without OpenAI dependency.
"""
import asyncio
import os

async def bhumi_integrated():
    """Using Bhumi's integrated approach with direct HTTP requests"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from bhumi.base import LLMConfig, create_llm
    
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyD3Xk1pxApMlieUQIH4nlRgGV6hzRXQ2vI")
    
    if api_key == "your-gemini-api-key-here":
        print("Please set your GEMINI_API_KEY environment variable")
        return
    
    config = LLMConfig(
        api_key=api_key,
        model="gemini/gemini-2.5-flash-preview-04-17"
    )
    
    llm = create_llm(config)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain to me how AI works"}
    ]
    
    response = await llm.completion(messages)
    print(response.get("text", ""))

if __name__ == "__main__":
    print("=== Bhumi integrated approach (no OpenAI dependency) ===")
    asyncio.run(bhumi_integrated())
