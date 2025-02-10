import asyncio
import os
import time
import psutil
import matplotlib.pyplot as plt
from datetime import datetime
from fastapi import FastAPI
import uvicorn
from bhumi.base_client import BaseLLMClient, LLMConfig
from google import genai
from openai import AsyncOpenAI
import aiohttp
import dotenv
from typing import List, Dict
import statistics
import httpx
import numpy as np
from pydantic import BaseModel

dotenv.load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash-8b"
OPENAI_MODEL = "gpt-4o-mini"
GROQ_MODEL = "mixtral-8x7b-32768"
MAX_CONCURRENT = 30
BATCH_SIZE = 10
NUM_CONCURRENT_REQUESTS = 15
NUM_TEST_RUNS = 1

# Initialize clients
genai_client = genai.Client(api_key=GEMINI_API_KEY)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Initialize Bhumi clients
bhumi_gemini_config = LLMConfig(
    api_key=GEMINI_API_KEY,
    model=f"gemini/{GEMINI_MODEL}",
    debug=False
)
bhumi_openai_config = LLMConfig(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    debug=False
)
bhumi_groq_config = LLMConfig(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    model=f"groq/{GROQ_MODEL}",
    debug=False
)

bhumi_gemini_client = BaseLLMClient(bhumi_gemini_config, max_concurrent=MAX_CONCURRENT)
bhumi_openai_client = BaseLLMClient(bhumi_openai_config, max_concurrent=MAX_CONCURRENT)
bhumi_groq_client = BaseLLMClient(bhumi_groq_config, max_concurrent=MAX_CONCURRENT)

# Test prompts
TEST_PROMPTS = [
    "What is 2+2?",
    "Name a color",
    "Say hello",
    "Count to 3",
    "Name a fruit"
]

# Create FastAPI apps
app_bhumi_gemini = FastAPI()
app_bhumi_openai = FastAPI()
app_bhumi_groq = FastAPI()
app_native_gemini = FastAPI()
app_native_openai = FastAPI()
app_native_groq = FastAPI()
app_raw_gemini = FastAPI()
app_raw_openai = FastAPI()
app_raw_groq = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# Bhumi Implementations
@app_bhumi_gemini.post("/generate")
async def generate_bhumi_gemini(request: PromptRequest):
    response = await bhumi_gemini_client.completion([
        {"role": "user", "content": request.prompt}
    ])
    return {"response": response["text"]}

@app_bhumi_openai.post("/generate")
async def generate_bhumi_openai(request: PromptRequest):
    response = await bhumi_openai_client.completion([
        {"role": "user", "content": request.prompt}
    ])
    return {"response": response["text"]}

@app_bhumi_groq.post("/generate")
async def generate_bhumi_groq(request: PromptRequest):
    response = await bhumi_groq_client.completion([
        {"role": "user", "content": request.prompt}
    ])
    return {"response": response["text"]}

# Native Client Implementations
@app_native_gemini.post("/generate")
async def generate_native_gemini(request: PromptRequest):
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=request.prompt
        )
    )
    return {"response": response.text}

@app_native_openai.post("/generate")
async def generate_native_openai(request: PromptRequest):
    response = await openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": request.prompt}]
    )
    return {"response": response.choices[0].message.content}

@app_native_groq.post("/generate")
async def generate_native_groq(request: PromptRequest):
    response = await groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": request.prompt}]
    )
    return {"response": response.choices[0].message.content}

# Raw HTTP Implementations
@app_raw_gemini.post("/generate")
async def generate_raw_gemini(request: PromptRequest):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{
            "parts": [{"text": request.prompt}],
            "role": "user"
        }]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, params=params, json=data) as resp:
            response = await resp.json()
            return {"response": response["candidates"][0]["content"]["parts"][0]["text"]}

@app_raw_openai.post("/generate")
async def generate_raw_openai(request: PromptRequest):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": request.prompt}]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            response = await resp.json()
            return {"response": response["choices"][0]["message"]["content"]}

@app_raw_groq.post("/generate")
async def generate_raw_groq(request: PromptRequest):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": request.prompt}]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            response = await resp.json()
            return {"response": response["choices"][0]["message"]["content"]}

# Add health check endpoints for all apps
for app in [app_bhumi_gemini, app_bhumi_openai, app_bhumi_groq, app_native_gemini, 
            app_native_openai, app_native_groq, app_raw_gemini, app_raw_openai, app_raw_groq]:
    @app.get("/health")
    async def health():
        return {"status": "ok"}

# Add test endpoints for all apps
for app in [app_bhumi_gemini, app_bhumi_openai, app_bhumi_groq, app_native_gemini, 
            app_native_openai, app_native_groq, app_raw_gemini, app_raw_openai, app_raw_groq]:
    @app.get("/test")
    async def test():
        return await app.post("/generate", json={"prompt": "test"})

async def load_test_server(port: int, num_requests: int) -> Dict:
    """Load test a server with concurrent requests"""
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        async def make_request(prompt: str):
            try:
                print(f"Sending request with prompt: {prompt}")
                response = await client.post(
                    f"http://localhost:{port}/generate",
                    json={"prompt": prompt},
                    timeout=30.0
                )
                
                print(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response body: {response.text}")
                    
                if response.status_code == 200:
                    return response.elapsed.total_seconds()
                else:
                    print(f"Request failed with status {response.status_code}")
                    return None
            except Exception as e:
                print(f"Request error: {str(e)}")
                return None
        
        # Make concurrent requests with delay between batches
        tasks = []
        batch_size = 5
        for i in range(0, num_requests, batch_size):
            batch_tasks = []
            for _ in range(min(batch_size, num_requests - i)):
                prompt = np.random.choice(TEST_PROMPTS)
                batch_tasks.append(make_request(prompt))
            
            batch_results = await asyncio.gather(*batch_tasks)
            tasks.extend(batch_results)
            await asyncio.sleep(0.5)
        
        response_times = [t for t in tasks if t is not None]
        
        end_time = time.time()
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            'total_time': end_time - start_time,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'peak_memory': peak_memory,
            'memory_increase': peak_memory - initial_memory,
            'successful_requests': len(response_times),
            'failed_requests': num_requests - len(response_times)
        }

async def verify_server(port: int) -> bool:
    """Verify server is up and responding"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:{port}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"Server verification failed: {str(e)}")
            return False

async def run_server_tests():
    """Run load tests for all implementations"""
    results = {
        'Bhumi (Gemini)': {'runs': []},
        'Bhumi (OpenAI)': {'runs': []},
        'Bhumi (Groq)': {'runs': []},
        'Native Gemini': {'runs': []},
        'Native OpenAI': {'runs': []},
        'Native Groq': {'runs': []},
        'Raw Gemini': {'runs': []},
        'Raw OpenAI': {'runs': []},
        'Raw Groq': {'runs': []}
    }
    
    ports = {
        'Bhumi (Gemini)': 8000,
        'Bhumi (OpenAI)': 8001,
        'Bhumi (Groq)': 8002,
        'Native Gemini': 8003,
        'Native OpenAI': 8004,
        'Native Groq': 8005,
        'Raw Gemini': 8006,
        'Raw OpenAI': 8007,
        'Raw Groq': 8008
    }
    
    apps = {
        'Bhumi (Gemini)': app_bhumi_gemini,
        'Bhumi (OpenAI)': app_bhumi_openai,
        'Bhumi (Groq)': app_bhumi_groq,
        'Native Gemini': app_native_gemini,
        'Native OpenAI': app_native_openai,
        'Native Groq': app_native_groq,
        'Raw Gemini': app_raw_gemini,
        'Raw OpenAI': app_raw_openai,
        'Raw Groq': app_raw_groq
    }
    
    for run in range(NUM_TEST_RUNS):
        print(f"\n🔄 Run {run + 1}/{NUM_TEST_RUNS}")
        
        for impl, port in ports.items():
            print(f"\n🚀 Testing {impl}...")
            
            config = uvicorn.Config(apps[impl], port=port, log_level="info")
            server = uvicorn.Server(config)
            server_task = asyncio.create_task(server.serve())
            
            await asyncio.sleep(2)
            if not await verify_server(port):
                print(f"❌ {impl} server failed to start properly")
                continue
            
            print(f"✅ {impl} server started successfully")
            
            try:
                # Test the endpoint first
                async with httpx.AsyncClient() as client:
                    test_response = await client.get(f"http://localhost:{port}/test")
                    print(f"Test response: {test_response.status_code}")
                    if test_response.status_code == 200:
                        print(f"Test content: {test_response.json()}")
                
                # Run load test
                results[impl]['runs'].append(
                    await load_test_server(port, NUM_CONCURRENT_REQUESTS)
                )
            finally:
                server.should_exit = True
                await server_task
                
            print(f"✅ {impl} test completed")
    
    # Calculate averages
    for impl in results:
        runs = results[impl]['runs']
        if runs:  # Only calculate if we have results
            results[impl]['avg_total_time'] = statistics.mean(r['total_time'] for r in runs)
            results[impl]['avg_response_time'] = statistics.mean(r['avg_response_time'] for r in runs)
            results[impl]['avg_peak_memory'] = statistics.mean(r['peak_memory'] for r in runs)
            results[impl]['avg_success_rate'] = statistics.mean(r['successful_requests']/NUM_CONCURRENT_REQUESTS * 100 for r in runs)
    
    return results

def plot_server_results(results: Dict):
    """Plot server benchmark results"""
    plt.figure(figsize=(20, 10))
    implementations = list(results.keys())
    colors = {
        'Bhumi (Gemini)': '#FF7F50',  # Coral
        'Bhumi (OpenAI)': '#FF4500',  # OrangeRed
        'Bhumi (Groq)': '#FFA07A',    # Light Salmon
        'Native Gemini': '#4285F4',   # Google Blue
        'Native OpenAI': '#00A67E',   # OpenAI Green
        'Native Groq': '#20B2AA',     # Light Sea Green
        'Raw Gemini': '#FF6B6B',      # Light Red
        'Raw OpenAI': '#98FB98',      # Light Green
        'Raw Groq': '#87CEEB'         # Sky Blue
    }
    
    # Create subplots with adjusted layout
    fig, axes = plt.subplots(2, 2, figsize=(20, 15))
    
    # Plot 1: Total Time (top left)
    times = [results[impl]['avg_total_time'] for impl in implementations]
    bars = axes[0, 0].bar(implementations, times, color=[colors[impl] for impl in implementations])
    axes[0, 0].set_title('Average Total Processing Time')
    axes[0, 0].set_ylabel('Time (seconds)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Plot 2: Response Time (top right)
    resp_times = [results[impl]['avg_response_time'] for impl in implementations]
    bars = axes[0, 1].bar(implementations, resp_times, color=[colors[impl] for impl in implementations])
    axes[0, 1].set_title('Average Response Time per Request')
    axes[0, 1].set_ylabel('Time (seconds)')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Plot 3: Memory Usage (bottom left)
    memory = [results[impl]['avg_peak_memory'] for impl in implementations]
    bars = axes[1, 0].bar(implementations, memory, color=[colors[impl] for impl in implementations])
    axes[1, 0].set_title('Average Peak Memory Usage')
    axes[1, 0].set_ylabel('Memory (MB)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Plot 4: Success Rate (bottom right)
    success_rates = [results[impl]['avg_success_rate'] for impl in implementations]
    bars = axes[1, 1].bar(implementations, success_rates, color=[colors[impl] for impl in implementations])
    axes[1, 1].set_title('Average Success Rate')
    axes[1, 1].set_ylabel('Success Rate (%)')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"llm_server_comparison_{timestamp}.png"
    plt.savefig(plot_filename, bbox_inches='tight')
    print(f"\n📈 Plot saved as: {plot_filename}")

if __name__ == "__main__":
    results = asyncio.run(run_server_tests())
    plot_server_results(results) 