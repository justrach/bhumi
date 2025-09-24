import os
import orjson
from typing import Dict, List, Optional, Tuple
import statistics
from satya import Model, Field

class SystemConfig(Model):
    """System configuration with Satya validation for fast parsing and validation"""
    buffer_size: int = Field(
        min_value=256, 
        max_value=1000000,
        description="Buffer size in bytes"
    )
    min_buffer: int = Field(
        min_value=64,  # More lenient minimum
        max_value=100000,
        description="Minimum buffer size"
    )
    max_buffer: int = Field(
        min_value=256,  # More lenient minimum
        max_value=2000000,
        description="Maximum buffer size"
    )
    adjustment_factor: float = Field(
        min_value=0.1,
        max_value=10.0,
        description="Buffer adjustment factor"
    )
    max_concurrent: int = Field(
        min_value=1,
        max_value=100,
        description="Maximum concurrent connections"
    )
    batch_size: int = Field(
        min_value=1,
        max_value=50,
        description="Batch processing size"
    )
    max_retries: int = Field(
        min_value=0,
        max_value=10,
        description="Maximum retry attempts"
    )
    retry_delay: float = Field(
        min_value=0.1,
        max_value=30.0,
        description="Delay between retries in seconds"
    )
    timeout: float = Field(
        min_value=1.0,
        max_value=300.0,
        description="Request timeout in seconds"
    )
    keepalive_timeout: float = Field(
        min_value=1.0,
        max_value=300.0,
        description="Keep-alive timeout in seconds"
    )

class ArchiveEntry(Model):
    """MAP-Elites archive entry with Satya v0.3.7 validation"""
    config: SystemConfig = Field(description="System configuration")
    performance: float = Field(
        ge=-1000.0,
        le=100000.0,
        description="Performance metric"
    )

class MapElitesArchive(Model):
    """Complete MAP-Elites archive structure with Satya v0.3.7 validation"""
    resolution: int = Field(
        ge=1,
        le=20,
        description="Archive grid resolution"
    )
    archive: Dict[str, ArchiveEntry] = Field(
        description="MAP-Elites archive entries keyed by coordinate tuples"
    )

class MapElitesBuffer:
    """Optimized buffer strategy using trained MAP-Elites archive with orjson + Satya v0.3.7 nested model validation"""
    
    def __init__(self, archive_path: str = "src/archive_latest.json"):
        self.current_size = 8192  # Default starting size
        self.chunk_history = []
        self.response_length = 0
        
        # Fast loading with orjson + Satya v0.3.7 nested model validation
        self._load_archive_fast(archive_path)
        
        # Get best overall config as fallback
        self.best_config = max(self.archive.values(), key=lambda x: x[1])[0]
        
    def _load_archive_fast(self, archive_path: str):
        """Fast archive loading with orjson and Satya v0.3.7 nested model validation"""
        try:
            # Use orjson for ultra-fast JSON parsing (2-3x faster than json)
            with open(archive_path, 'rb') as f:
                raw_data = orjson.loads(f.read())

            # Use Satya v0.3.7's enhanced nested model validation
            # This now supports Dict[str, ArchiveEntry] structures!
            try:
                archive_model = MapElitesArchive(**raw_data)

                # Convert to our internal format with parsed tuples
                self.archive = {}

                for coord_str, entry in archive_model.archive.items():
                    # Parse coordinate tuple safely (e.g., "(1, 3, 0)" -> (1, 3, 0))
                    coord_tuple = self._parse_coordinate_tuple(coord_str)

                    # Store as tuple key with SystemConfig and performance
                    # entry.config is already a validated SystemConfig instance
                    # entry.performance is already validated as float
                    self.archive[coord_tuple] = (entry.config, entry.performance)

                print(f"✅ Successfully loaded {len(self.archive)} archive entries using Satya v0.3.7 nested model validation")

            except Exception as validation_error:
                print(f"Satya validation failed ({validation_error}), falling back to manual validation...")
                self._load_archive_fallback(archive_path)

        except Exception as e:
            # Fallback to slower method if fast loading fails
            print(f"Fast loading failed ({e}), falling back to standard JSON...")
            self._load_archive_fallback(archive_path)
    
    def _parse_coordinate_tuple(self, coord_str: str) -> Tuple[int, int, int]:
        """Safely parse coordinate tuple string without eval()"""
        # Remove parentheses and split by comma
        clean_str = coord_str.strip('()')
        parts = [int(x.strip()) for x in clean_str.split(',')]
        
        if len(parts) != 3:
            raise ValueError(f"Invalid coordinate format: {coord_str}")
            
        return tuple(parts)
    
    def _load_archive_fallback(self, archive_path: str):
        """Fallback loading method using standard json"""
        import json
        
        with open(archive_path) as f:
            data = json.load(f)
            
        # Convert archive back from serialized format
        self.archive = {}
        for k, v in data["archive"].items():
            coord_tuple = eval(k)  # Keep eval for fallback compatibility
            # Convert dict to SystemConfig using Satya
            config = SystemConfig(**v["config"])
            self.archive[coord_tuple] = (config, v["performance"])
        
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

    def get_performance_info(self) -> Dict:
        """Get performance information about the loaded archive"""
        total_entries = len(self.archive)
        valid_entries = sum(1 for _, (_, perf) in self.archive.items() if perf > 0)
        avg_performance = statistics.mean(perf for _, (_, perf) in self.archive.items() if perf > 0) if valid_entries > 0 else 0
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "optimization_coverage": valid_entries / total_entries if total_entries > 0 else 0,
            "average_performance": avg_performance,
            "best_performance": max((perf for _, (_, perf) in self.archive.items()), default=0)
        } 