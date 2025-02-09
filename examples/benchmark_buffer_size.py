import time
import asyncio
import statistics
from bhumi.base_client import BaseLLMClient, LLMConfig
import matplotlib.pyplot as plt
import os
from datetime import datetime

async def test_buffer_size(buffer_size: int, num_requests: int = 10) -> float:
    """Test performance with a specific buffer size"""
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        buffer_size=buffer_size  # We'll need to add this to LLMConfig
    )
    client = BaseLLMClient(config)
    
    # Test prompt that will generate a decent-sized response
    prompt = "Write a detailed paragraph about artificial intelligence."
    
    # Measure response times
    times = []
    for _ in range(num_requests):
        start = time.perf_counter()
        response = await client.completion([
            {"role": "user", "content": prompt}
        ])
        times.append(time.perf_counter() - start)
    
    return statistics.mean(times)

async def find_optimal_buffer():
    """Test different buffer sizes and plot results"""
    # Test buffer sizes from 1KB to 1MB
    buffer_sizes = [
        1024,        # 1KB
        4096,        # 4KB
        8192,        # 8KB
        16384,       # 16KB
        32768,       # 32KB
        65536,       # 64KB
        131072,      # 128KB
        262144,      # 256KB
        524288,      # 512KB
        1048576,     # 1MB
    ]
    
    results = []
    for size in buffer_sizes:
        print(f"Testing buffer size: {size/1024:.1f}KB")
        avg_time = await test_buffer_size(size)
        results.append(avg_time)
        
    # Plot results
    plt.figure(figsize=(12, 6))
    plt.semilogx(buffer_sizes, results, marker='o')
    plt.grid(True)
    plt.xlabel('Buffer Size (bytes)')
    plt.ylabel('Average Response Time (seconds)')
    plt.title('Response Time vs Buffer Size')
    
    # Add size labels
    for size, time in zip(buffer_sizes, results):
        plt.annotate(f'{size/1024:.1f}KB\n{time:.3f}s', 
                    (size, time), 
                    textcoords="offset points", 
                    xytext=(0,10), 
                    ha='center')
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"benchmarks/plots/buffer_size_benchmark_{timestamp}.png"
    os.makedirs("benchmarks/plots", exist_ok=True)
    plt.savefig(plot_filename, bbox_inches='tight')
    print(f"\n📈 Plot saved as: {plot_filename}")
    
    # Find optimal size
    optimal_idx = results.index(min(results))
    optimal_size = buffer_sizes[optimal_idx]
    print(f"\nOptimal buffer size: {optimal_size/1024:.1f}KB")
    print(f"Best average response time: {results[optimal_idx]:.3f}s")

if __name__ == "__main__":
    asyncio.run(find_optimal_buffer()) 