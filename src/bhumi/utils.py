import asyncio
from functools import wraps
import logging
from typing import TypeVar, Callable, Any

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