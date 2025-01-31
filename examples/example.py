import os
from bhumi import Bhumi

# API Keys
OPENAI_KEY = os.environ['OPENAI_API_KEY']
GEMINI_KEY = os.environ['GEMINI_API_KEY']
# Example prompt
prompt = "Explain what a neural network is in one sentence."

# OpenAI example
openai_client = Bhumi(
    max_concurrent=10,
    provider="openai",
    model="gpt-4o-mini",
    debug=True
)
openai_response = openai_client.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    api_key=OPENAI_KEY
)
print("\n🤖 OpenAI Response:")
print(openai_response.text)

gemini_client = Bhumi(
    max_concurrent=10,
    provider="gemini",
    model="gemini-1.5-flash-8b",
    debug=True
)
gemini_response = gemini_client.completion(
    model="gemini/gemini-1.5-flash-8b",
    messages=[{"role": "user", "content": prompt}],
    api_key=GEMINI_KEY
)
print("\n🤖 Gemini Response:")
print(gemini_response.text)

print("\n✨ Supported Models:")
print("OpenAI:")
print("  - gpt-4o-mini")
print("\nAnthropic:")
print("  - claude-3-haiku")
print("\nGemini:")
print("  - gemini-1.5-flash-8b")
print("  - gemini-1.5-ultra") 