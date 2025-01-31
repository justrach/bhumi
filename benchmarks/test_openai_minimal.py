import os
import json
from bhumi.bhumi import BhumiCore
import time
import dotenv


API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"

def test_openai_minimal():
    """Test bare OpenAI implementation"""
    print("\n🚀 Testing minimal OpenAI implementation...")
    
    # Initialize core with debug mode
    core = BhumiCore(
        max_concurrent=1,
        provider="openai",
        model=MODEL,
        debug=True
    )
    
    # Simple test prompt
    prompt = "Write a haiku about coding"
    
    # Prepare request
    request = {
        "_headers": {
            "Authorization": API_KEY
        },
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    print(f"\nSending prompt: '{prompt}'")
    print(f"Request payload: {json.dumps(request, indent=2)}")
    
    # Submit request
    core._submit(json.dumps(request))
    
    # Wait for response
    start_time = time.time()
    while True:
        if response := core._get_response():
            print("\nReceived response:")
            print("=" * 40)
            print(response)
            print("=" * 40)
            print(f"\nResponse time: {time.time() - start_time:.2f}s")
            break
        elif time.time() - start_time > 30:  # 30 second timeout
            print("❌ Timeout waiting for response")
            break
        time.sleep(0.1)

if __name__ == "__main__":
    test_openai_minimal() 