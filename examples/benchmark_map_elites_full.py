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
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import random
from concurrent.futures import ThreadPoolExecutor
import itertools

dotenv.load_dotenv()

@dataclass
class SystemConfig:
    """Full system configuration including buffer, concurrency, and retry settings"""
    # Buffer settings
    buffer_size: int
    min_buffer: int
    max_buffer: int
    adjustment_factor: float
    
    # Concurrency settings
    max_concurrent: int
    batch_size: int
    
    # Retry settings
    max_retries: int
    retry_delay: float
    
    # Network settings
    timeout: float
    keepalive_timeout: float
    
    def mutate(self, mutation_rate=0.2) -> 'SystemConfig':
        """Create a mutated copy of this config"""
        return SystemConfig(
            # Buffer mutations
            buffer_size=int(self.buffer_size * random.uniform(1-mutation_rate, 1+mutation_rate)),
            min_buffer=int(self.min_buffer * random.uniform(1-mutation_rate, 1+mutation_rate)),
            max_buffer=int(self.max_buffer * random.uniform(1-mutation_rate, 1+mutation_rate)),
            adjustment_factor=self.adjustment_factor * random.uniform(1-mutation_rate, 1+mutation_rate),
            
            # Concurrency mutations
            max_concurrent=max(1, int(self.max_concurrent * random.uniform(1-mutation_rate, 1+mutation_rate))),
            batch_size=max(1, int(self.batch_size * random.uniform(1-mutation_rate, 1+mutation_rate))),
            
            # Retry mutations
            max_retries=max(1, int(self.max_retries * random.uniform(1-mutation_rate, 1+mutation_rate))),
            retry_delay=max(0.1, self.retry_delay * random.uniform(1-mutation_rate, 1+mutation_rate)),
            
            # Network mutations
            timeout=max(1.0, self.timeout * random.uniform(1-mutation_rate, 1+mutation_rate)),
            keepalive_timeout=max(1.0, self.keepalive_timeout * random.uniform(1-mutation_rate, 1+mutation_rate))
        )

class FullMapElites:
    """MAP-Elites archive for full system configurations"""
    def __init__(self, resolution: int = 5):
        self.resolution = resolution
        self.archive: Dict[Tuple[int, int, int], Tuple[SystemConfig, float]] = {}
        self.history: List[Dict] = []
        
    def save(self, filename: str = None):
        """Save the archive and history to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmarks/map_elites/archive_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert archive to serializable format
        archive_data = {
            str(k): {
                "config": asdict(v[0]),  # Convert dataclass to dict
                "performance": v[1]
            }
            for k, v in self.archive.items()
        }
        
        data = {
            "resolution": self.resolution,
            "archive": archive_data,
            "history": self.history
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 MAP-Elites archive saved to: {filename}")
    
    @classmethod
    def load(cls, filename: str) -> 'FullMapElites':
        """Load archive from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        map_elites = cls(resolution=data["resolution"])
        
        # Convert back from serialized format
        map_elites.archive = {
            eval(k): (
                SystemConfig(**v["config"]),
                v["performance"]
            )
            for k, v in data["archive"].items()
        }
        
        map_elites.history = data["history"]
        return map_elites

    def add(self, config: SystemConfig, metrics: Dict) -> bool:
        """Add configuration if it improves performance for its behavioral niche"""
        # Discretize the behavior space
        load_bin = min(self.resolution-1, int(metrics["concurrent_requests"] / 5))
        size_bin = min(self.resolution-1, int(metrics["avg_response_size"] / 1000))
        error_bin = min(self.resolution-1, int(metrics["error_rate"] * self.resolution))
        behavior = (load_bin, size_bin, error_bin)
        
        performance = metrics["throughput"] * (1 - metrics["error_rate"])
        
        improved = False
        if behavior not in self.archive or performance > self.archive[behavior][1]:
            self.archive[behavior] = (config, performance)
            improved = True
        
        # Track history
        self.history.append({
            "behavior": behavior,
            "performance": performance,
            "metrics": metrics,
            "improved": improved
        })
        
        return improved

    def get_elite(self, response_length: int, num_chunks: int) -> Optional[SystemConfig]:
        """Get the best configuration for given characteristics"""
        # Discretize the behavior space
        size_bin = min(self.resolution-1, int(response_length / 1000))
        chunk_bin = min(self.resolution-1, num_chunks)
        
        # Try to find exact match
        for (load, size, error), (config, _) in self.archive.items():
            if size == size_bin and chunk_bin == load:
                return config
        
        # If no exact match, find nearest neighbor
        if not self.archive:
            return None
            
        # Find closest match based on response size and chunk count
        closest = min(
            self.archive.items(),
            key=lambda x: (
                abs(x[0][1] - size_bin) + 
                abs(x[0][0] - chunk_bin)
            )
        )
        
        return closest[1][0]  # Return the config from closest match

async def benchmark_system(config: SystemConfig, prompts: List[str], num_iterations: int = 3) -> Dict:
    """Benchmark a system configuration under various conditions"""
    results = []
    errors = 0
    total_requests = 0
    
    client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4o-mini",
        buffer_size=config.buffer_size,
    ), max_concurrent=config.max_concurrent)
    
    start_time = time.perf_counter()
    
    # Process prompts in parallel batches
    for _ in range(num_iterations):
        # Create batches of concurrent requests
        batches = [prompts[i:i + config.batch_size] 
                  for i in range(0, len(prompts), config.batch_size)]
        
        for batch in batches:
            tasks = []
            for prompt in batch:
                total_requests += 1
                tasks.append(
                    client.completion([
                        {"role": "user", "content": prompt}
                    ])
                )
            
            # Run batch concurrently
            try:
                batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
                for response in batch_responses:
                    if isinstance(response, Exception):
                        errors += 1
                        continue
                    
                    try:
                        stats = json.loads(response["raw_response"]["text"])
                        results.append({
                            "response_size": len(stats["text"]),
                            "num_chunks": len(stats.get("chunk_sizes", [])),
                            "avg_chunk_size": statistics.mean(stats.get("chunk_sizes", [0]))
                        })
                    except Exception as e:
                        errors += 1
                        print(f"Error processing response: {e}")
            
            except Exception as e:
                errors += 1
                print(f"Batch error: {e}")
    
    elapsed = time.perf_counter() - start_time
    
    if not results:
        return {
            "throughput": 0,
            "error_rate": 1.0,
            "concurrent_requests": config.max_concurrent,
            "avg_response_size": 0
        }
    
    return {
        "throughput": sum(r["response_size"] for r in results) / elapsed,
        "error_rate": errors / total_requests,
        "concurrent_requests": config.max_concurrent,
        "avg_response_size": statistics.mean(r["response_size"] for r in results),
        "avg_chunks": statistics.mean(r["num_chunks"] for r in results),
        "avg_chunk_size": statistics.mean(r["avg_chunk_size"] for r in results)
    }

async def train_map_elites(prompts: List[str], generations: int = 4, population_size: int = 5):
    """Train MAP-Elites archive with parallel evaluation"""
    map_elites = FullMapElites()
    
    # Reduce prompts to essential test cases
    test_prompts = [
        "Write a short sentence.",  # Test small responses
        "Write a detailed paragraph about AI.",  # Test medium responses
        "Write a long story about time travel."  # Test large responses
    ]
    
    # Initial population - smaller but more diverse
    configs = [
        SystemConfig(
            # Small buffer, high concurrency
            buffer_size=2048,
            min_buffer=1024,
            max_buffer=8192,
            adjustment_factor=1.5,
            max_concurrent=5,
            batch_size=3,
            max_retries=2,
            retry_delay=0.5,
            timeout=30.0,
            keepalive_timeout=60.0
        ),
        # Medium buffer, medium concurrency
        SystemConfig(
            buffer_size=16384,
            min_buffer=4096,
            max_buffer=32768,
            adjustment_factor=1.3,
            max_concurrent=3,
            batch_size=2,
            max_retries=3,
            retry_delay=1.0,
            timeout=45.0,
            keepalive_timeout=90.0
        ),
        # Large buffer, low concurrency
        SystemConfig(
            buffer_size=65536,
            min_buffer=32768,
            max_buffer=131072,
            adjustment_factor=1.2,
            max_concurrent=1,
            batch_size=1,
            max_retries=4,
            retry_delay=1.5,
            timeout=60.0,
            keepalive_timeout=120.0
        ),
        # Dynamic small chunks
        SystemConfig(
            buffer_size=4096,
            min_buffer=1024,
            max_buffer=16384,
            adjustment_factor=2.0,
            max_concurrent=4,
            batch_size=2,
            max_retries=2,
            retry_delay=0.5,
            timeout=30.0,
            keepalive_timeout=60.0
        ),
        # Balanced configuration
        SystemConfig(
            buffer_size=32768,
            min_buffer=8192,
            max_buffer=65536,
            adjustment_factor=1.5,
            max_concurrent=2,
            batch_size=2,
            max_retries=3,
            retry_delay=1.0,
            timeout=45.0,
            keepalive_timeout=90.0
        )
    ]
    
    for generation in range(generations):
        print(f"\nGeneration {generation + 1}/{generations}")
        
        # Use single iteration for early generations
        iterations = 1 if generation < generations-1 else 2
        
        # Evaluate configs in parallel
        tasks = [benchmark_system(config, test_prompts, num_iterations=iterations) 
                for config in configs]
        metrics_list = await asyncio.gather(*tasks)
        
        # Update archive
        for config, metrics in zip(configs, metrics_list):
            map_elites.add(config, metrics)
            print(f"Config performance: {metrics['throughput']:.0f} chars/s")
            print(f"Error rate: {metrics['error_rate']:.2%}")
        
        # Create new population through targeted mutation
        if generation < generations - 1:
            # Get best performing configs
            best_configs = sorted(
                map_elites.archive.values(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Create new configs through focused mutation
            configs = []
            for parent, _ in best_configs:
                # Add slightly mutated version
                configs.append(parent.mutate(mutation_rate=0.1))
                # Add more experimental version
                configs.append(parent.mutate(mutation_rate=0.3))
            
            # Keep population size constant
            while len(configs) < population_size:
                configs.append(random.choice(best_configs)[0].mutate(mutation_rate=0.2))
    
    return map_elites

def plot_evolution(map_elites: FullMapElites):
    """Plot the evolution of the system performance"""
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Performance over time
    plt.subplot(2, 2, 1)
    history_df = pd.DataFrame(map_elites.history)
    plt.plot(history_df["performance"])
    plt.title("Performance Evolution")
    plt.xlabel("Evaluation")
    plt.ylabel("Performance")
    
    # Plot 2: Error rates
    plt.subplot(2, 2, 2)
    plt.plot(history_df["metrics"].apply(lambda x: x["error_rate"]))
    plt.title("Error Rate Evolution")
    plt.xlabel("Evaluation")
    plt.ylabel("Error Rate")
    
    # Plot 3: Throughput heatmap
    plt.subplot(2, 2, 3)
    matrix = np.zeros((map_elites.resolution, map_elites.resolution))
    for (load, size, _), (_, perf) in map_elites.archive.items():
        matrix[load, size] = perf
    
    sns.heatmap(matrix, cmap='viridis')
    plt.title("Performance Landscape")
    plt.xlabel("Response Size")
    plt.ylabel("Concurrent Load")
    
    # Plot 4: Configuration distribution
    plt.subplot(2, 2, 4)
    buffer_sizes = [config.buffer_size for config, _ in map_elites.archive.values()]
    plt.hist(buffer_sizes, bins=20)
    plt.title("Buffer Size Distribution")
    plt.xlabel("Buffer Size")
    plt.ylabel("Count")
    
    plt.tight_layout()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"benchmarks/plots/system_evolution_{timestamp}.png"
    os.makedirs("benchmarks/plots", exist_ok=True)
    plt.savefig(plot_path, bbox_inches='tight')
    print(f"\n📈 Evolution plot saved as: {plot_path}")

async def main():
    prompts = [
        "Write a one-sentence summary.",
        "Write a detailed paragraph about artificial intelligence.",
        "Explain quantum computing in detail.",
        "Write a short story about time travel.",
        "Describe the entire plot of Star Wars.",
    ]
    
    # Train MAP-Elites with parallel evaluation
    map_elites = await train_map_elites(prompts, generations=5, population_size=20)
    plot_evolution(map_elites)
    map_elites.save()
    
    # Print best configurations
    print("\nBest configurations by scenario:")
    for (load, size, error), (config, perf) in sorted(
        map_elites.archive.items(),
        key=lambda x: x[1][1],
        reverse=True
    )[:5]:
        print(f"\nLoad level: {load}, Response size: {size}k chars, Error rate: {error/map_elites.resolution:.1%}")
        print(f"Performance: {perf:.0f} chars/s")
        print(f"Buffer size: {config.buffer_size}")
        print(f"Concurrency: {config.max_concurrent}")
        print(f"Batch size: {config.batch_size}")

if __name__ == "__main__":
    asyncio.run(main()) 