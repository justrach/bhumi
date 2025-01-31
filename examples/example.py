import os
from bhumi.client import GeminiClient, AnthropicClient, OpenAIClient
import asyncio

# API Keys

# Example prompt
prompt = "Explain what a neural network is in one sentence."

# Initialize clients
gemini_client = GeminiClient(max_concurrent=10)
# anthropic_client = AnthropicClient(max_concurrent=10)
openai_client = OpenAIClient(max_concurrent=10)  # Set max_concurrent to 1 like working example

async def main():
    # Gemini example with different models
    for model in ["gemini-1.5-flash-8b", "gemini-1.5-ultra"]:
        response = await gemini_client.acompletion(
            model=f"gemini/{model}",
            messages=[{"role": "user", "content": prompt}],
            api_key=GEMINI_KEY
        )
        print(f"\n🤖 Gemini ({model}) Response:")
        print(response.text)

    # # Anthropic example
    # anthropic_response = anthropic_client.completion(
    #     model="anthropic/claude-3-haiku",
    #     messages=[{"role": "user", "content": prompt}],
    #     api_key=ANTHROPIC_KEY
    # )
    # print("\n🤖 Anthropic Response:")
    # print(anthropic_response.text)

    # OpenAI example with different models
    for model in ["gpt-4o"]:  # Just test with one model first
        response = await openai_client.acompletion(
            model=model,  # Don't add openai/ prefix
            messages=[{"role": "user", "content": prompt}],
            api_key=OPENAI_KEY
        )
        print(f"\n🤖 OpenAI ({model}) Response:")
        print(response.text)

    # Print supported models
    print("\n✨ Supported Models:")
    print("OpenAI:")
    print("  - gpt-4")
    print("  - gpt-3.5-turbo")
    print("\nAnthropic:")
    print("  - claude-3-haiku")
    print("\nGemini:")
    print("  - gemini-1.5-flash-8b")
    print("  - gemini-1.5-ultra")

if __name__ == "__main__":
    asyncio.run(main()) 