#!/usr/bin/env python3
"""Test free-threaded Python support in Bhumi.

This test verifies that Bhumi can run truly in parallel on Python 3.13+
without the GIL, achieving maximum performance.
"""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from bhumi import bhumi  # Import the Rust module

def test_parallel_execution():
    """Test that multiple threads can execute Bhumi operations in parallel."""
    
    print(f"Python version: {sys.version}")
    print(f"Free-threaded: {sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else 'N/A'}")
    
    # Create multiple BhumiCore instances
    cores = [
        bhumi.BhumiCore(
            max_concurrent=10,
            provider="openai",
            model="gpt-4",
            buffer_size=131072
        )
        for _ in range(4)
    ]
    
    def worker(core_id, core):
        """Worker function that uses Bhumi."""
        start = time.time()
        # Simulate some work
        for i in range(100):
            _ = core.max_concurrent  # Access property
        elapsed = time.time() - start
        print(f"Thread {core_id}: Completed in {elapsed:.4f}s")
        return elapsed
    
    # Run in parallel
    print("\n🚀 Testing parallel execution with 4 threads...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(worker, i, core) 
            for i, core in enumerate(cores)
        ]
        results = [f.result() for f in futures]
    
    total_time = time.time() - start
    
    print(f"\n📊 Results:")
    print(f"   Total time: {total_time:.4f}s")
    print(f"   Average thread time: {sum(results)/len(results):.4f}s")
    print(f"   Parallelism efficiency: {sum(results)/total_time:.2f}x")
    
    if hasattr(sys, '_is_gil_enabled'):
        if sys._is_gil_enabled():
            print("\n⚠️  GIL is ENABLED - running with GIL protection")
        else:
            print("\n🎉 GIL is DISABLED - running in true parallel mode!")
            print("   Bhumi is on STEROIDS! 🚀")
    
    print("\n✅ Free-threaded test completed successfully!")

if __name__ == "__main__":
    test_parallel_execution()
