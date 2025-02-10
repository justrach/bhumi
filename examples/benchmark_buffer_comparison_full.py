import time
import asyncio
import statistics
from bhumi.base_client import BaseLLMClient, LLMConfig
import matplotlib.pyplot as plt
import os
from datetime import datetime
import json
import numpy as np
import seaborn as sns
import pandas as pd
import dotenv
from dataclasses import dataclass
from typing import Dict, List, Tuple
import random
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_map_elites_full import SystemConfig, FullMapElites, benchmark_system

dotenv.load_dotenv()

class SimpleBuffer:
    """Fixed size buffer"""
    def __init__(self, size: int):
        self.size = size
        
    def get_size(self) -> int:
        return self.size

class DynamicBuffer:
    """Original dynamic buffer implementation"""
    def __init__(self, initial_size=8192, min_size=1024, max_size=131072):
        self.current_size = initial_size
        self.min_size = min_size
        self.max_size = max_size
        self.chunk_history = []
        self.adjustment_factor = 1.5
        
    def get_size(self) -> int:
        return self.current_size
        
    def adjust(self, chunk_size):
        self.chunk_history.append(chunk_size)
        recent_chunks = self.chunk_history[-5:]
        avg_chunk = statistics.mean(recent_chunks) if recent_chunks else chunk_size
        
        if avg_chunk > self.current_size * 0.8:
            self.current_size = min(
                self.max_size,
                int(self.current_size * self.adjustment_factor)
            )
        elif avg_chunk < self.current_size * 0.3:
            self.current_size = max(
                self.min_size,
                int(self.current_size / self.adjustment_factor)
            )
        return self.current_size

async def benchmark_buffer_strategy(buffer_strategy, prompts: List[str], num_iterations: int = 3) -> Dict:
    """Benchmark a specific buffer strategy"""
    results = []
    errors = 0
    total_requests = 0
    
    if isinstance(buffer_strategy, str) and buffer_strategy == "map_elites":
        # Load the saved MAP-Elites archive
        map_elites = FullMapElites.load("/Users/rachpradhan/bhumi/benchmarks/map_elites/archive_latest.json")
        
        # Get the best overall configuration
        best_config = max(map_elites.archive.values(), key=lambda x: x[1])[0]
        buffer_size = best_config.buffer_size
        
        # For adaptive behavior, we can also use the archive during runtime
        def get_adaptive_config(response_length: int, num_chunks: int) -> int:
            if elite_config := map_elites.get_elite(response_length, num_chunks):
                return elite_config.buffer_size
            return buffer_size  # fallback to best overall
            
    else:
        buffer_size = buffer_strategy.get_size()
    
    client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        buffer_size=buffer_size
    ))
    
    start_time = time.perf_counter()
    
    for _ in range(num_iterations):
        for prompt in prompts:
            total_requests += 1
            try:
                response = await client.completion([
                    {"role": "user", "content": prompt}
                ])
                
                stats = json.loads(response["raw_response"]["text"])
                chunk_sizes = stats.get("chunk_sizes", [])
                
                if isinstance(buffer_strategy, DynamicBuffer):
                    for chunk_size in chunk_sizes:
                        buffer_strategy.adjust(chunk_size)
                elif isinstance(buffer_strategy, str) and buffer_strategy == "map_elites":
                    # Use MAP-Elites archive for adaptive sizing
                    buffer_size = get_adaptive_config(
                        len(stats["text"]),
                        len(chunk_sizes)
                    )
                
                results.append({
                    "response_size": len(stats["text"]),
                    "num_chunks": len(chunk_sizes),
                    "avg_chunk_size": statistics.mean(chunk_sizes) if chunk_sizes else 0,
                    "buffer_size": buffer_size
                })
                
            except Exception as e:
                errors += 1
                print(f"Error: {e}")
    
    elapsed = time.perf_counter() - start_time
    
    if not results:
        return {
            "throughput": 0,
            "error_rate": 1.0,
            "avg_response_size": 0,
            "buffer_utilization": 0
        }
    
    return {
        "throughput": sum(r["response_size"] for r in results) / elapsed,
        "error_rate": errors / total_requests,
        "avg_response_size": statistics.mean(r["response_size"] for r in results),
        "buffer_utilization": statistics.mean(r["avg_chunk_size"] / r["buffer_size"] for r in results),
        "avg_chunks": statistics.mean(r["num_chunks"] for r in results),
        "avg_chunk_size": statistics.mean(r["avg_chunk_size"] for r in results)
    }

def plot_comparison(results: Dict[str, List[Dict]]):
    """Create comparison visualizations"""
    plt.figure(figsize=(15, 12))
    
    # Convert results to DataFrame
    df = pd.DataFrame([
        {
            "Strategy": strategy,
            **metric
        }
        for strategy, metrics in results.items()
        for metric in metrics
    ])
    
    # Plot 1: Throughput comparison
    plt.subplot(2, 2, 1)
    sns.boxplot(data=df, x="Strategy", y="throughput")
    plt.title("Throughput Comparison")
    plt.ylabel("Characters per Second")
    
    # Plot 2: Error rates
    plt.subplot(2, 2, 2)
    sns.boxplot(data=df, x="Strategy", y="error_rate")
    plt.title("Error Rate Comparison")
    plt.ylabel("Error Rate")
    
    # Plot 3: Buffer utilization
    plt.subplot(2, 2, 3)
    sns.boxplot(data=df, x="Strategy", y="buffer_utilization")
    plt.title("Buffer Utilization")
    plt.ylabel("Utilization Ratio")
    
    # Plot 4: Response size vs throughput
    plt.subplot(2, 2, 4)
    for strategy in df["Strategy"].unique():
        strategy_data = df[df["Strategy"] == strategy]
        plt.scatter(
            strategy_data["avg_response_size"],
            strategy_data["throughput"],
            label=strategy,
            alpha=0.6
        )
    plt.title("Response Size vs Throughput")
    plt.xlabel("Response Size (chars)")
    plt.ylabel("Throughput (chars/s)")
    plt.legend()
    
    plt.tight_layout()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"benchmarks/plots/buffer_comparison_full_{timestamp}.png"
    os.makedirs("benchmarks/plots", exist_ok=True)
    plt.savefig(plot_path, bbox_inches='tight')
    print(f"\n📈 Plot saved as: {plot_path}")
    
    # Save detailed results
    csv_path = f"benchmarks/results/buffer_comparison_full_{timestamp}.csv"
    os.makedirs("benchmarks/results", exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"📊 Detailed results saved as: {csv_path}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    summary = df.groupby("Strategy").agg({
        "throughput": ["mean", "std"],
        "error_rate": ["mean", "std"],
        "buffer_utilization": ["mean", "std"]
    }).round(3)
    print(summary)

async def main():
    prompts = [
        "Write a short sentence.",  # Small response
        "Write a detailed paragraph about AI.",  # Medium response
        "Write a long story about time travel."  # Large response
    ]  # Reduced to 3 essential prompts
    
    strategies = {
        "Fixed (128KB)": SimpleBuffer(131072),
        "Dynamic": DynamicBuffer(),
        "MAP-Elites": "map_elites"
    }
    
    # Reduce iterations for statistical significance while keeping costs reasonable
    num_runs = 3  # Reduced from 5
    num_iterations = 2  # Reduced from 3
    
    # Run all strategies and their iterations in parallel
    tasks = []
    for name, strategy in strategies.items():
        for run in range(num_runs):
            tasks.append((name, strategy, run))
    
    print(f"\nRunning {len(tasks)} benchmarks in parallel...")
    # New total: 3 strategies * 3 runs * 2 iterations * 3 prompts = 54 calls
    
    results = {}
    
    # Create and gather all tasks
    benchmark_tasks = [
        benchmark_buffer_strategy(strategy, prompts)
        for name, strategy, _ in tasks
    ]
    
    # Run all benchmarks concurrently
    metrics_list = await asyncio.gather(*benchmark_tasks)
    
    # Organize results by strategy
    for (name, _, _), metrics in zip(tasks, metrics_list):
        if name not in results:
            results[name] = []
        results[name].append(metrics)
        
        # Print progress
        print(f"{name} - Throughput: {metrics['throughput']:.0f} chars/s, "
              f"Error rate: {metrics['error_rate']:.2%}")
    
    plot_comparison(results)

if __name__ == "__main__":
    asyncio.run(main()) 