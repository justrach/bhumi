import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import statistics

@dataclass
class SystemConfig:
    buffer_size: int
    min_buffer: int
    max_buffer: int
    adjustment_factor: float
    max_concurrent: int
    batch_size: int
    max_retries: int
    retry_delay: float
    timeout: float
    keepalive_timeout: float

class MapElitesBuffer:
    """Buffer strategy using trained MAP-Elites archive"""
    def __init__(self, archive_path: str = "src/archive_latest"):
        self.current_size = 8192  # Default starting size
        self.chunk_history = []
        self.response_length = 0
        
        # Load archive
        with open(archive_path) as f:
            data = json.load(f)
            
        # Convert archive back from serialized format
        self.archive = {
            eval(k): (
                SystemConfig(**v["config"]),
                v["performance"]
            )
            for k, v in data["archive"].items()
        }
        
        # Get best overall config as fallback
        self.best_config = max(self.archive.values(), key=lambda x: x[1])[0]
        
    def get_size(self) -> int:
        return self.current_size
        
    def adjust(self, chunk_size: int):
        """Adjust buffer size based on MAP-Elites archive"""
        self.chunk_history.append(chunk_size)
        self.response_length += chunk_size
        
        # Get current characteristics
        num_chunks = len(self.chunk_history)
        
        # Get elite configuration for current scenario
        size_bin = min(4, int(self.response_length / 1000))
        chunk_bin = min(4, num_chunks)
        
        # Try exact match first
        for (load, size, error), (config, perf) in self.archive.items():
            if size == size_bin and chunk_bin == load and perf > 0:
                self.current_size = config.buffer_size
                return self.current_size
                
        # If no exact match, find nearest neighbor with good performance
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
            
            for (load, size, _), (config, _) in neighbors:
                distance = abs(size - size_bin) + abs(chunk_bin - load)
                weight = 1 / (distance + 1)
                total_weight += weight
                weighted_size += config.buffer_size * weight
            
            self.current_size = int(weighted_size / total_weight)
        else:
            # Fall back to best overall config
            self.current_size = self.best_config.buffer_size
            
        return self.current_size 