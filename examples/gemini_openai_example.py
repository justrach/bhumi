#!/usr/bin/env python3
"""
Example showing how to use Gemini with OpenAI-compatible endpoint
This matches the example you provided in your request.
"""
import asyncio
import os
from openai import AsyncOpenAI

async def direct_openai_compatible():
    """Direct usage with OpenAI client (as shown in your request)"""
    
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyD3Xk1pxApMlieUQIH4nlRgGV6hzRXQ2vI")
    
    if api_key == "your-gemini-api-key-here":
        print("Please set your GEMINI_API_KEY environment variable")
        return
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    response = await client.chat.completions.create(
        model="gemini-2.5-flash-preview-04-17",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Explain to me how AI works"
            }
        ]
    )

    print(response.choices[0].message.content)

async def bhumi_integrated():
    """Using Bhumi's integrated approach"""
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
    print("=== Direct OpenAI-compatible approach ===")
    asyncio.run(direct_openai_compatible())
    
    print("\n=== Bhumi integrated approach ===")
    asyncio.run(bhumi_integrated())
