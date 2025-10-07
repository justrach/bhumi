#!/usr/bin/env python3
"""
Benchmark: OpenAI Library vs Bhumi
Compare performance between the official OpenAI library and Bhumi
"""

import os
import sys
import time
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import statistics

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

# Test if gpt-5-nano exists
print("🔍 Checking if gpt-5-nano model exists...")
try:
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    # Try to list models or make a test call
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print("✅ gpt-5-nano model exists and is accessible!")
        MODEL = "gpt-5-nano"
    except openai.NotFoundError:
        print("⚠️  gpt-5-nano not found, falling back to gpt-4o-mini")
        MODEL = "gpt-4o-mini"
    except Exception as e:
        print(f"⚠️  Error testing gpt-5-nano: {e}")
        print("   Falling back to gpt-4o-mini")
        MODEL = "gpt-4o-mini"
except ImportError:
    print("❌ OpenAI library not installed. Installing...")
    os.system("pip install openai")
    import openai
    MODEL = "gpt-4o-mini"

print(f"\n📊 Using model: {MODEL}\n")

# Test messages
TEST_MESSAGES = [
    [{"role": "user", "content": "What is 2+2?"}],
    [{"role": "user", "content": "Name a color"}],
    [{"role": "user", "content": "Say hello"}],
    [{"role": "user", "content": "What is Python?"}],
    [{"role": "user", "content": "Name a fruit"}],
]

# ============================================================================
# OpenAI Library Benchmark
# ============================================================================

def benchmark_openai_sync(num_requests: int = 5):
    """Benchmark OpenAI library with synchronous requests"""
    print(f"🔵 OpenAI Library (Sync) - {num_requests} requests")
    
    client = openai.OpenAI(api_key=api_key)
    times = []
    
    for i in range(num_requests):
        start = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=TEST_MESSAGES[i % len(TEST_MESSAGES)],
            max_tokens=50
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"   Request {i+1}: {elapsed:.3f}s - {response.choices[0].message.content[:50]}...")
    
    print(f"   ⏱️  Total: {sum(times):.3f}s, Avg: {statistics.mean(times):.3f}s")
    return times

async def benchmark_openai_async(num_requests: int = 5):
    """Benchmark OpenAI library with async requests"""
    print(f"\n🔵 OpenAI Library (Async) - {num_requests} requests")
    
    client = openai.AsyncOpenAI(api_key=api_key)
    times = []
    
    async def make_request(i):
        start = time.time()
        response = await client.chat.completions.create(
            model=MODEL,
            messages=TEST_MESSAGES[i % len(TEST_MESSAGES)],
            max_tokens=50
        )
        elapsed = time.time() - start
        return elapsed, response.choices[0].message.content
    
    # Run all requests concurrently
    start_total = time.time()
    results = await asyncio.gather(*[make_request(i) for i in range(num_requests)])
    total_time = time.time() - start_total
    
    for i, (elapsed, content) in enumerate(results):
        times.append(elapsed)
        print(f"   Request {i+1}: {elapsed:.3f}s - {content[:50]}...")
    
    print(f"   ⏱️  Total: {total_time:.3f}s, Avg: {statistics.mean(times):.3f}s")
    print(f"   🚀 Speedup from concurrency: {sum(times)/total_time:.2f}x")
    return times, total_time

# ============================================================================
# Bhumi Benchmark
# ============================================================================

def benchmark_bhumi_sync(num_requests: int = 5):
    """Benchmark Bhumi with synchronous requests"""
    print(f"\n🟢 Bhumi (Sync) - {num_requests} requests")
    
    try:
        from bhumi import BaseLLMClient, LLMConfig
    except ImportError:
        print("❌ Bhumi not installed properly")
        return []
    
    config = LLMConfig(
        api_key=api_key,
        model=f"openai/{MODEL}"
    )
    client = BaseLLMClient(config)
    times = []
    
    for i in range(num_requests):
        start = time.time()
        response = asyncio.run(client.completion(
            messages=TEST_MESSAGES[i % len(TEST_MESSAGES)],
            max_tokens=50
        ))
        elapsed = time.time() - start
        times.append(elapsed)
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"   Request {i+1}: {elapsed:.3f}s - {content[:50]}...")
    
    print(f"   ⏱️  Total: {sum(times):.3f}s, Avg: {statistics.mean(times):.3f}s")
    return times

async def benchmark_bhumi_async(num_requests: int = 5):
    """Benchmark Bhumi with async requests"""
    print(f"\n🟢 Bhumi (Async) - {num_requests} requests")
    
    try:
        from bhumi import BaseLLMClient, LLMConfig
    except ImportError:
        print("❌ Bhumi not installed properly")
        return [], 0
    
    config = LLMConfig(
        api_key=api_key,
        model=f"openai/{MODEL}"
    )
    client = BaseLLMClient(config)
    times = []
    
    async def make_request(i):
        start = time.time()
        response = await client.completion(
            messages=TEST_MESSAGES[i % len(TEST_MESSAGES)],
            max_tokens=50
        )
        elapsed = time.time() - start
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        return elapsed, content
    
    # Run all requests concurrently
    start_total = time.time()
    results = await asyncio.gather(*[make_request(i) for i in range(num_requests)])
    total_time = time.time() - start_total
    
    for i, (elapsed, content) in enumerate(results):
        times.append(elapsed)
        print(f"   Request {i+1}: {elapsed:.3f}s - {content[:50]}...")
    
    print(f"   ⏱️  Total: {total_time:.3f}s, Avg: {statistics.mean(times):.3f}s")
    print(f"   🚀 Speedup from concurrency: {sum(times)/total_time:.2f}x")
    return times, total_time

# ============================================================================
# Free-Threaded Benchmark (Python 3.13+)
# ============================================================================

def benchmark_bhumi_free_threaded(num_requests: int = 5):
    """Benchmark Bhumi with free-threaded Python (no GIL)"""
    
    if not hasattr(sys, '_is_gil_enabled'):
        print("\n⚠️  Free-threaded Python not available (requires Python 3.13+)")
        return []
    
    if sys._is_gil_enabled():
        print("\n⚠️  GIL is enabled - skipping free-threaded benchmark")
        return []
    
    print(f"\n🚀 Bhumi (Free-Threaded - NO GIL) - {num_requests} requests")
    
    try:
        from bhumi import BaseLLMClient, LLMConfig
    except ImportError:
        print("❌ Bhumi not installed properly")
        return []
    
    # Create separate clients for each thread
    configs = [
        LLMConfig(api_key=api_key, model=f"openai/{MODEL}")
        for _ in range(num_requests)
    ]
    clients = [BaseLLMClient(config) for config in configs]
    
    def make_request(i, client):
        start = time.time()
        response = asyncio.run(client.completion(
            messages=TEST_MESSAGES[i % len(TEST_MESSAGES)],
            max_tokens=50
        ))
        elapsed = time.time() - start
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        return elapsed, content
    
    # Run in parallel threads (no GIL!)
    start_total = time.time()
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        results = list(executor.map(lambda i: make_request(i, clients[i]), range(num_requests)))
    total_time = time.time() - start_total
    
    times = []
    for i, (elapsed, content) in enumerate(results):
        times.append(elapsed)
        print(f"   Request {i+1}: {elapsed:.3f}s - {content[:50]}...")
    
    print(f"   ⏱️  Total: {total_time:.3f}s, Avg: {statistics.mean(times):.3f}s")
    print(f"   🚀 Speedup from parallelism: {sum(times)/total_time:.2f}x")
    print(f"   💪 TRUE PARALLEL EXECUTION - NO GIL!")
    return times

# ============================================================================
# Main Benchmark
# ============================================================================

def main():
    print("=" * 70)
    print("🏁 BENCHMARK: OpenAI Library vs Bhumi")
    print("=" * 70)
    print(f"Model: {MODEL}")
    print(f"Python: {sys.version}")
    if hasattr(sys, '_is_gil_enabled'):
        print(f"GIL: {'Enabled' if sys._is_gil_enabled() else 'DISABLED (Free-threaded)'}")
    print("=" * 70)
    
    num_requests = 5
    
    # Run benchmarks
    print("\n📋 Running benchmarks...\n")
    
    # OpenAI sync
    oai_sync_times = benchmark_openai_sync(num_requests)
    
    # OpenAI async
    oai_async_times, oai_async_total = asyncio.run(benchmark_openai_async(num_requests))
    
    # Bhumi sync
    bhumi_sync_times = benchmark_bhumi_sync(num_requests)
    
    # Bhumi async
    bhumi_async_times, bhumi_async_total = asyncio.run(benchmark_bhumi_async(num_requests))
    
    # Bhumi free-threaded (if available)
    bhumi_ft_times = benchmark_bhumi_free_threaded(num_requests)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print(f"\n🔵 OpenAI Library:")
    print(f"   Sync:  {sum(oai_sync_times):.3f}s total, {statistics.mean(oai_sync_times):.3f}s avg")
    print(f"   Async: {oai_async_total:.3f}s total, {statistics.mean(oai_async_times):.3f}s avg")
    
    if bhumi_sync_times:
        print(f"\n🟢 Bhumi:")
        print(f"   Sync:  {sum(bhumi_sync_times):.3f}s total, {statistics.mean(bhumi_sync_times):.3f}s avg")
        print(f"   Async: {bhumi_async_total:.3f}s total, {statistics.mean(bhumi_async_times):.3f}s avg")
        
        # Comparison
        print(f"\n⚡ Performance Comparison:")
        sync_speedup = sum(oai_sync_times) / sum(bhumi_sync_times)
        async_speedup = oai_async_total / bhumi_async_total
        print(f"   Sync:  Bhumi is {sync_speedup:.2f}x {'faster' if sync_speedup > 1 else 'slower'}")
        print(f"   Async: Bhumi is {async_speedup:.2f}x {'faster' if async_speedup > 1 else 'slower'}")
    
    if bhumi_ft_times:
        print(f"\n🚀 Bhumi Free-Threaded (NO GIL):")
        print(f"   This is the FUTURE of Python performance!")
        print(f"   True parallel execution across all CPU cores")
    
    print("\n" + "=" * 70)
    print("✅ Benchmark complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
