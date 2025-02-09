import asyncio
import os
import time
import psutil
import matplotlib.pyplot as plt
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from bhumi.base_client import BaseLLMClient, LLMConfig
from google import genai
import aiohttp
import dotenv
from typing import List, Dict
import statistics
import httpx
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

dotenv.load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-1.5-flash-8b"
MAX_CONCURRENT = 30
BATCH_SIZE = 10
NUM_CONCURRENT_REQUESTS = 15  # Number of concurrent requests to simulate
NUM_TEST_RUNS = 2  # Number of times to run the complete test

# Initialize clients
genai_client = genai.Client(api_key=API_KEY)
bhumi_config = LLMConfig(
    api_key=API_KEY,
    model=f"gemini/{MODEL}",
    debug=False
)
bhumi_client = BaseLLMClient(bhumi_config, max_concurrent=MAX_CONCURRENT)

# Test prompts (shorter queries for stress testing)
TEST_PROMPTS = [
    "What is 2+2?",
    "Name a color",
    "Say hello",
    "Count to 3",
    "Name a fruit"
]

# Create FastAPI apps for each implementation
app_bhumi = FastAPI()
app_genai = FastAPI()
app_native = FastAPI()

# Add request model
class PromptRequest(BaseModel):
    prompt: str

# Bhumi Implementation
@app_bhumi.post("/generate")
async def generate_bhumi(request: PromptRequest):
    response = await bhumi_client.completion([
        {"role": "user", "content": request.prompt}
    ])
    return {"response": response["text"]}

# Google GenAI Implementation
@app_genai.post("/generate")
async def generate_genai(request: PromptRequest):
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: genai_client.models.generate_content(
            model=MODEL,
            contents=request.prompt
        )
    )
    return {"response": response.text}

# Native HTTP Implementation
@app_native.post("/generate")
async def generate_native(request: PromptRequest):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
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

# Add health check endpoints
@app_bhumi.get("/health")
async def health_bhumi():
    return {"status": "ok"}

@app_genai.get("/health")
async def health_genai():
    return {"status": "ok"}

@app_native.get("/health")
async def health_native():
    return {"status": "ok"}

# Add test endpoints
@app_bhumi.get("/test")
async def test_bhumi():
    return await generate_bhumi(PromptRequest(prompt="test"))

@app_genai.get("/test")
async def test_genai():
    return await generate_genai(PromptRequest(prompt="test"))

@app_native.get("/test")
async def test_native():
    return await generate_native(PromptRequest(prompt="test"))

async def load_test_server(port: int, num_requests: int) -> Dict:
    """Load test a server with concurrent requests"""
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        async def make_request(prompt: str):
            try:
                # Print request data for debugging
                print(f"Sending request with prompt: {prompt}")
                
                response = await client.post(
                    f"http://localhost:{port}/generate",
                    json={"prompt": prompt},  # Make sure this matches PromptRequest model
                    timeout=30.0
                )
                
                # Print response for debugging
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
        batch_size = 5  # Process requests in smaller batches
        for i in range(0, num_requests, batch_size):
            batch_tasks = []
            for _ in range(min(batch_size, num_requests - i)):
                prompt = np.random.choice(TEST_PROMPTS)
                batch_tasks.append(make_request(prompt))
            
            # Run batch and collect results
            batch_results = await asyncio.gather(*batch_tasks)
            tasks.extend(batch_results)
            
            # Small delay between batches
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
        'Bhumi': {'runs': []},
        'Google GenAI': {'runs': []},
        'Native HTTP': {'runs': []}
    }
    
    ports = {
        'Bhumi': 8000,
        'Google GenAI': 8001,
        'Native HTTP': 8002
    }
    
    for run in range(NUM_TEST_RUNS):
        print(f"\n🔄 Run {run + 1}/{NUM_TEST_RUNS}")
        
        for impl, port in ports.items():
            print(f"\n🚀 Testing {impl}...")
            
            # Start server in background
            config = None
            if impl == 'Bhumi':
                config = uvicorn.Config(app_bhumi, port=port, log_level="info")  # Changed to info for debugging
            elif impl == 'Google GenAI':
                config = uvicorn.Config(app_genai, port=port, log_level="info")
            else:
                config = uvicorn.Config(app_native, port=port, log_level="info")
            
            server = uvicorn.Server(config)
            server_task = asyncio.create_task(server.serve())
            
            # Wait for server to start and verify it's responding
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
        results[impl]['avg_total_time'] = statistics.mean(r['total_time'] for r in runs)
        results[impl]['avg_response_time'] = statistics.mean(r['avg_response_time'] for r in runs)
        results[impl]['avg_peak_memory'] = statistics.mean(r['peak_memory'] for r in runs)
        results[impl]['avg_success_rate'] = statistics.mean(r['successful_requests']/NUM_CONCURRENT_REQUESTS * 100 for r in runs)
    
    return results

def plot_server_results(results: Dict):
    """Plot server benchmark results"""
    plt.figure(figsize=(20, 5))
    implementations = list(results.keys())
    colors = {
        'Bhumi': '#FF7F50',
        'Google GenAI': '#4285F4',
        'Native HTTP': '#FF6B6B'
    }
    
    # Plot 1: Average Total Time
    plt.subplot(1, 4, 1)
    times = [results[impl]['avg_total_time'] for impl in implementations]
    bars = plt.bar(implementations, times, color=[colors[impl] for impl in implementations])
    plt.title('Average Total Processing Time')
    plt.ylabel('Time (seconds)')
    plt.xticks(rotation=45, ha='right')
    for bar, val in zip(bars, times):
        plt.text(bar.get_x() + bar.get_width()/2, val, 
                f'{val:.2f}s', ha='center', va='bottom')
    
    # Plot 2: Average Response Time
    plt.subplot(1, 4, 2)
    resp_times = [results[impl]['avg_response_time'] for impl in implementations]
    bars = plt.bar(implementations, resp_times, color=[colors[impl] for impl in implementations])
    plt.title('Average Response Time per Request')
    plt.ylabel('Time (seconds)')
    plt.xticks(rotation=45, ha='right')
    for bar, val in zip(bars, resp_times):
        plt.text(bar.get_x() + bar.get_width()/2, val, 
                f'{val:.2f}s', ha='center', va='bottom')
    
    # Plot 3: Memory Usage
    plt.subplot(1, 4, 3)
    memory = [results[impl]['avg_peak_memory'] for impl in implementations]
    bars = plt.bar(implementations, memory, color=[colors[impl] for impl in implementations])
    plt.title('Average Peak Memory Usage')
    plt.ylabel('Memory (MB)')
    plt.xticks(rotation=45, ha='right')
    for bar, val in zip(bars, memory):
        plt.text(bar.get_x() + bar.get_width()/2, val, 
                f'{val:.1f}MB', ha='center', va='bottom')
    
    # Plot 4: Success Rate
    plt.subplot(1, 4, 4)
    success_rates = [results[impl]['avg_success_rate'] for impl in implementations]
    bars = plt.bar(implementations, success_rates, color=[colors[impl] for impl in implementations])
    plt.title('Average Success Rate')
    plt.ylabel('Success Rate (%)')
    plt.xticks(rotation=45, ha='right')
    for bar, val in zip(bars, success_rates):
        plt.text(bar.get_x() + bar.get_width()/2, val, 
                f'{val:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"gemini_server_comparison_{timestamp}.png"
    plt.savefig(plot_filename)
    print(f"\n📈 Plot saved as: {plot_filename}")

if __name__ == "__main__":
    results = asyncio.run(run_server_tests())
    plot_server_results(results) 