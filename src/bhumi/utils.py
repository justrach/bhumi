import asyncio
from functools import wraps
import logging
from typing import TypeVar, Callable, Any
import os

T = TypeVar('T')

def async_retry(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    exponential_base: float = 2,
    logger: logging.Logger = None,
):
    """
    Retry decorator for async functions with exponential backoff
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for retry in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if logger:
                        logger.warning(f"Attempt {retry + 1} failed: {str(e)}")
                    if retry < max_retries:
                        if logger:
                            logger.info(f"Retrying in {delay:.1f} seconds...")
                        await asyncio.sleep(delay)
                        delay *= exponential_base
                    
            raise last_exception
            
        return wrapper
    return decorator 

def check_performance_optimization():
    """
    Check if Bhumi is using optimized MAP-Elites archive for best performance.
    Returns a dict with optimization status and recommendations.
    """
    
    # Look for MAP-Elites archive in multiple locations (same as base_client.py)
    archive_paths = [
        # Installed package location
        os.path.join(os.path.dirname(__file__), "data", "archive_latest.json"),
        # Development locations
        "src/archive_latest.json",
        "benchmarks/map_elites/archive_latest.json",
        os.path.join(os.path.dirname(__file__), "../archive_latest.json"),
        os.path.join(os.path.dirname(__file__), "../../benchmarks/map_elites/archive_latest.json")
    ]
    
    archive_found = None
    archive_size = 0
    
    for path in archive_paths:
        if os.path.exists(path):
            archive_found = path
            archive_size = os.path.getsize(path)
            break
    
    if not archive_found:
        return {
            "optimized": False,
            "status": "❌ No MAP-Elites archive found",
            "message": "Using fallback dynamic buffer - performance may be suboptimal",
            "recommendation": "Install the full Bhumi package or contact support for performance optimization archive"
        }
    
    # Check if archive is reasonably sized (good archives are typically >100KB)
    if archive_size < 100000:  # 100KB
        return {
            "optimized": False,
            "status": "⚠️ Small MAP-Elites archive detected",
            "message": f"Archive found ({archive_size // 1024}KB) but appears incomplete",
            "archive_path": archive_found,
            "recommendation": "Consider updating to latest Bhumi version for better performance"
        }
    
    return {
        "optimized": True,
        "status": "✅ Optimized MAP-Elites archive loaded",
        "message": f"Using high-performance buffer ({archive_size // 1024}KB archive)",
        "archive_path": archive_found,
        "recommendation": "Performance optimization active - no action needed"
    }

def print_performance_status():
    """Print a user-friendly performance optimization status"""
    status = check_performance_optimization()
    
    print("🚀 Bhumi Performance Status")
    print("=" * 40)
    print(f"{status['status']}")
    print(f"📝 {status['message']}")
    
    if 'archive_path' in status:
        print(f"📂 Archive: {status['archive_path']}")
        
        # Try to load and show additional performance info
        try:
            from .map_elites_buffer import MapElitesBuffer
            buffer = MapElitesBuffer(status['archive_path'])
            perf_info = buffer.get_performance_info()
            
            print(f"⚡ Optimization Details:")
            print(f"   • Entries: {perf_info['total_entries']:,} total, {perf_info['valid_entries']:,} optimized")
            print(f"   • Coverage: {perf_info['optimization_coverage']:.1%} of search space")
            print(f"   • Performance: {perf_info['average_performance']:.1f} avg, {perf_info['best_performance']:.1f} best")
            print(f"   • Loading: Satya validation + orjson parsing (3x faster)")
            
        except Exception as e:
            print(f"   ⚠️ Could not load performance details: {e}")
    
    print(f"💡 {status['recommendation']}")
    
    return status['optimized'] 