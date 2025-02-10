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
        self.illumination_history: List[Dict] = []  # Track grid coverage
        
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
            "history": self.history,
            "illumination_history": self.illumination_history  # Add illumination
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
        map_elites.illumination_history = data.get("illumination_history", [])
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
        
        # Track history and illumination
        current_illumination = {
            "total_cells": self.resolution ** 3,
            "filled_cells": len(self.archive),
            "coverage": len(self.archive) / (self.resolution ** 3),
            "mean_performance": np.mean([perf for _, perf in self.archive.values()]),
            "max_performance": max([perf for _, perf in self.archive.values()], default=0),
            "timestamp": datetime.now().isoformat()
        }
        
        self.illumination_history.append(current_illumination)
        print(f"\n🔦 Grid Coverage: {current_illumination['coverage']:.1%}")
        print(f"📊 Mean Performance: {current_illumination['mean_performance']:.0f}")
        
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
        size_bin = min(self.resolution-1, int(response_length / 1000))
        chunk_bin = min(self.resolution-1, num_chunks)
        
        # Try exact match first
        for (load, size, error), (config, perf) in self.archive.items():
            if size == size_bin and chunk_bin == load:
                if perf > 0:  # Only return if it's performing well
                    return config
        
        # If no exact match or poor performance, try to interpolate between nearest neighbors
        if self.archive:
            # Only consider cells with non-zero performance
            good_neighbors = [
                (k, v) for k, v in self.archive.items()
                if v[1] > 0  # Only use cells with positive performance
            ]
            
            if good_neighbors:
                neighbors = sorted(
                    good_neighbors,
                    key=lambda x: (
                        (x[0][1] - size_bin) ** 2 +  
                        (x[0][0] - chunk_bin) ** 2
                    )
                )[:3]
                
                # Weight configs by inverse distance
                total_weight = 0
                weighted_size = 0
                weighted_concurrent = 0
                weighted_batch = 0
                
                for (load, size, _), (config, _) in neighbors:
                    distance = abs(size - size_bin) + abs(chunk_bin - load)
                    weight = 1 / (distance + 1)
                    total_weight += weight
                    weighted_size += config.buffer_size * weight
                    weighted_concurrent += config.max_concurrent * weight
                    weighted_batch += config.batch_size * weight
                
                # Get min/max values from configs directly
                neighbor_configs = [config for (_, (config, _)) in neighbors]
                
                # Create interpolated config
                return SystemConfig(
                    buffer_size=int(weighted_size / total_weight),
                    min_buffer=min(c.min_buffer for c in neighbor_configs),
                    max_buffer=max(c.max_buffer for c in neighbor_configs),
                    adjustment_factor=1.5,
                    max_concurrent=max(1, int(weighted_concurrent / total_weight)),
                    batch_size=max(1, int(weighted_batch / total_weight)),
                    max_retries=3,
                    retry_delay=1.0,
                    timeout=30.0,
                    keepalive_timeout=60.0
                )
        
        # Fall back to dynamic buffer for empty or poor performing cells
        return SystemConfig(
            buffer_size=8192,  # Start with moderate size
            min_buffer=1024,
            max_buffer=131072,
            adjustment_factor=1.5,
            max_concurrent=max(1, min(chunk_bin * 2, 10)),  # Scale concurrency with load
            batch_size=max(1, min(chunk_bin, 5)),
            max_retries=3,
            retry_delay=0.5,
            timeout=30.0,
            keepalive_timeout=60.0
        )

    def plot_illumination(self):
        """Plot illumination progress"""
        plt.figure(figsize=(15, 5))
        
        # Plot 1: Coverage over time
        plt.subplot(1, 3, 1)
        coverage = [x["coverage"] for x in self.illumination_history]
        plt.plot(coverage)
        plt.title("Grid Coverage")
        plt.xlabel("Evaluations")
        plt.ylabel("Coverage %")
        
        # Plot 2: Mean performance
        plt.subplot(1, 3, 2)
        mean_perf = [x["mean_performance"] for x in self.illumination_history]
        plt.plot(mean_perf)
        plt.title("Mean Performance")
        plt.xlabel("Evaluations")
        plt.ylabel("Chars/s")
        
        # Plot 3: Current grid state
        plt.subplot(1, 3, 3)
        grid = np.zeros((self.resolution, self.resolution))
        for (load, size, _), (_, perf) in self.archive.items():
            grid[load, size] = perf
        
        sns.heatmap(grid, cmap='viridis', annot=True, fmt='.0f')
        plt.title(f"Performance Grid\n{len(self.archive)}/{self.resolution**3} cells")
        plt.xlabel("Response Size")
        plt.ylabel("Concurrent Load")
        
        plt.tight_layout()
        
        # Save illumination plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = f"benchmarks/plots/illumination_{timestamp}.png"
        os.makedirs("benchmarks/plots", exist_ok=True)
        plt.savefig(plot_path, bbox_inches='tight')
        print(f"\n💡 Illumination plot saved as: {plot_path}")

async def benchmark_system(config: SystemConfig, prompts: List[str], num_iterations: int = 3) -> Dict:
    """Benchmark a system configuration under various conditions"""
    results = []
    errors = 0
    total_requests = 0
    
    client = BaseLLMClient(LLMConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini/gemini-2.0-flash",
        buffer_size=config.buffer_size,
        debug=False # Enable debug in LLMConfig
    ), max_concurrent=config.max_concurrent, debug=False)  # Enable debug in client
    
    start_time = time.perf_counter()
    
    print(f"\nStarting benchmark with buffer_size={config.buffer_size}, max_concurrent={config.max_concurrent}")
    
    # Process prompts in parallel batches
    for iteration in range(num_iterations):
        print(f"\nIteration {iteration + 1}/{num_iterations}")
        batches = [prompts[i:i + config.batch_size] 
                  for i in range(0, len(prompts), config.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"\nProcessing batch {batch_idx + 1}/{len(batches)}")
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
                for resp_idx, response in enumerate(batch_responses):
                    if isinstance(response, Exception):
                        errors += 1
                        print(f"Request error for prompt {resp_idx}: {str(response)}")
                        continue
                    
                    try:
                        print(f"\nProcessing response {resp_idx}:")
                        print(f"Response type: {type(response)}")
                        print(f"Response content: {response}")
                        
                        # Just get the text field - the base_client already handles the extraction
                        text = response.get("text", "")
                        if text:
                            results.append({
                                "response_size": len(text),
                                "num_chunks": 1,  # Default for non-streaming
                                "avg_chunk_size": len(text)  # Single chunk for non-streaming
                            })
                            print(f"Successfully processed response. Length: {len(text)}")
                        else:
                            errors += 1
                            print(f"Empty response text. Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
                            
                    except Exception as e:
                        errors += 1
                        print(f"Error processing response {resp_idx}: {str(e)}")
                        print(f"Response type: {type(response)}")
                        if isinstance(response, dict):
                            print(f"Response keys: {response.keys()}")
                            print(f"Response content: {response}")
            
            except Exception as e:
                errors += 1
                print(f"Batch error in batch {batch_idx}: {e}")
    
    elapsed = time.perf_counter() - start_time
    
    print(f"\nBenchmark complete:")
    print(f"Total requests: {total_requests}")
    print(f"Successful responses: {len(results)}")
    print(f"Errors: {errors}")
    print(f"Time elapsed: {elapsed:.2f}s")
    
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

async def train_map_elites(prompts: List[str], generations: int = 8, population_size: int = 30):
    """Train MAP-Elites with enhanced evaluation strategy"""
    
    # Load existing archive with adaptive resolution
    try:
        map_elites = FullMapElites.load("benchmarks/map_elites/archive_latest.json")
        print("\n📥 Loaded existing MAP-Elites archive")
        # Keep more existing solutions for stability
        existing_configs = [config for config, _ in sorted(
            map_elites.archive.values(),
            key=lambda x: x[1],
            reverse=True
        )[:population_size//3]]  # Increased from //4 to //3
        
    except (FileNotFoundError, json.JSONDecodeError):
        map_elites = FullMapElites()
        existing_configs = []
        print("\n🆕 Creating new MAP-Elites archive")
    
    # Enhanced test prompts with more diversity
    test_prompts = {
        0: [  # Tiny responses (0-100 chars)
            "Hi!", "Yes.", "List 3 colors.",
            "Count to five.", "Write one word.",
            "What's 2+2?", "Name a planet."
        ],
        1: [  # Small responses (100-500 chars)
            "Write a tweet.", "Explain what is AI.",
            "Write a haiku.", "List 10 fruits.",
            "Define quantum.", "Describe your day.",
            "Write a short joke.", "Explain colors to a blind person."
        ],
        2: [  # Medium (500-2000 chars)
            "Write a short story.", "Explain how a car works.",
            "Write a product review.", "List 50 numbers.",
            "Describe a complex emotion.", "Explain photosynthesis.",
            "Write a scene description.", "Compare two philosophies."
        ],
        3: [  # Large (2000-5000 chars)
            "Write a technical spec.", "Explain quantum physics.",
            "Write a research summary.", "List 200 prime numbers.",
            "Analyze a classic novel.", "Explain blockchain.",
            "Write a detailed tutorial.", "Compare historical events."
        ],
        4: [  # Huge (5000+ chars)
            "Write a detailed essay.", "Explain the history of AI.",
            "Write a full story.", "Generate a large dataset.",
            "Write a scientific paper.", "Explain human consciousness.",
            "Write a comprehensive guide.", "Analyze multiple philosophical theories."
        ]
    }
    
    # Create systematic grid-filling configurations with adaptive sizing
    base_configs = []
    
    # For each load level (0-4)
    for load_level in range(5):
        concurrency = load_level * 2 + 1  # 1, 3, 5, 7, 9
        
        # For each size level (0-4), create multiple variants
        for size_level in range(5):
            base_size = 2 ** (10 + size_level)  # 1KB to 16KB base sizes
            
            # Create multiple variants per cell with different characteristics
            variants = [
                (base_size, 1.5),  # Standard
                (base_size * 1.5, 1.8),  # Larger buffer, more aggressive
                (base_size * 0.8, 1.3),  # Smaller buffer, more conservative
            ]
            
            for buf_size, adj_factor in variants:
                base_configs.append(SystemConfig(
                    buffer_size=int(buf_size),
                    min_buffer=int(buf_size * 0.5),
                    max_buffer=int(buf_size * 4),
                    adjustment_factor=adj_factor,
                    max_concurrent=concurrency,
                    batch_size=min(5, concurrency),
                    max_retries=3,
                    retry_delay=0.5,
                    timeout=30.0,
                    keepalive_timeout=60.0
                ))
    
    # Combine strategies with weighted selection
    configs = (
        existing_configs +  # Keep best performers
        base_configs +      # Add grid-filling configs
        [config.mutate(mutation_rate=0.2) for config in existing_configs[:5]] +  # Small mutations of best
        [config.mutate(mutation_rate=0.4) for config in existing_configs[5:10]] +  # Larger mutations
        [random.choice(base_configs).mutate(mutation_rate=0.3) 
         for _ in range(population_size - len(existing_configs) - len(base_configs))]
    )[:population_size]
    
    # Training loop with enhanced evaluation
    for generation in range(generations):
        print(f"\nGeneration {generation + 1}/{generations}")
        print(f"Testing {len(configs)} configurations across {sum(len(prompts) for prompts in test_prompts.values())} prompts")
        
        # Evaluate each config multiple times for stability
        tasks = []
        for config in configs:
            # Test each config against all prompt sizes
            for size_level, prompts in test_prompts.items():
                # Multiple iterations for stability
                tasks.append(benchmark_system(config, prompts, num_iterations=3))
        
        metrics_list = await asyncio.gather(*tasks)
        
        # Average results for each config
        config_metrics = {}
        for i, config in enumerate(configs):
            config_results = metrics_list[i::len(configs)]
            avg_metrics = {
                "throughput": statistics.mean(m["throughput"] for m in config_results),
                "error_rate": statistics.mean(m["error_rate"] for m in config_results),
                "concurrent_requests": statistics.mean(m["concurrent_requests"] for m in config_results),
                "avg_response_size": statistics.mean(m["avg_response_size"] for m in config_results)
            }
            config_metrics[config] = avg_metrics
        
        # Update archive with averaged results
        for config, metrics in config_metrics.items():
            map_elites.add(config, metrics)
        
        # Plot and save progress
        map_elites.plot_illumination()
        map_elites.save("benchmarks/map_elites/archive_latest.json")
        
        # Create next generation with adaptive strategy
        if generation < generations - 1:
            configs = create_next_generation(map_elites, population_size)
    
    return map_elites

def create_next_generation(map_elites: FullMapElites, population_size: int) -> List[SystemConfig]:
    """Create next generation with adaptive strategy"""
    # Identify empty and underperforming cells
    empty_cells = set(
        (load, size, error)
        for load in range(5)
        for size in range(5)
        for error in range(5)
    ) - set(map_elites.archive.keys())
    
    # Get best performers
    best_configs = [config for config, _ in sorted(
        map_elites.archive.values(),
        key=lambda x: x[1],
        reverse=True
    )[:population_size//4]]
    
    # Create targeted configs for empty cells
    targeted_configs = []
    for load, size, _ in empty_cells:
        base_size = 2 ** (10 + size)
        for adjustment in [0.8, 1.0, 1.2]:
            targeted_configs.append(SystemConfig(
                buffer_size=int(base_size * adjustment),
                min_buffer=int(base_size * adjustment * 0.5),
                max_buffer=int(base_size * adjustment * 2),
                adjustment_factor=1.5,
                max_concurrent=load * 2 + 1,
                batch_size=min(5, load * 2 + 1),
                max_retries=3,
                retry_delay=0.5,
                timeout=30.0,
                keepalive_timeout=60.0
            ))
    
    # Create new generation with multiple strategies
    new_gen = (
        best_configs[:5] +  # Keep top performers unchanged
        [config.mutate(0.1) for config in best_configs[:8]] +  # Small mutations
        [config.mutate(0.3) for config in best_configs[8:]] +  # Larger mutations
        targeted_configs[:population_size//4] +  # Add some targeted configs
        [random.choice(best_configs).mutate(0.2) 
         for _ in range(population_size - len(best_configs) * 2 - len(targeted_configs[:population_size//4]))]
    )
    
    return new_gen[:population_size]

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
    map_elites = await train_map_elites(
        prompts, 
        generations=8,  # More generations
        population_size=25  # Larger population
    )
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