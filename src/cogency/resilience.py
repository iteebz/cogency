"""
LLM Resilience: Simple timeout + retry for LLM calls.

WHAT IT DOES:
- Timeout Protection: Hard timeouts prevent hanging
- Retry Logic: Exponential backoff with jitter on failures
- Graceful Degradation: Returns helpful messages instead of crashes

USAGE:
@safe  # Just add this to LLM functions
async def my_llm_call():
    return await openai.chat.completions.create(...)

FEATURES:
✅ 30 second timeouts with 3 retries
✅ Exponential backoff: 0.5s → 1s → 2s → up to 10s max
✅ Jitter prevents thundering herd
✅ Zero configuration needed
"""

import asyncio
import time
import random
from functools import wraps
from typing import Dict, Callable, Awaitable, Any
from dataclasses import dataclass


@dataclass
class SafeConfig:
    """Configuration for @safe decorator - tune for your needs."""
    timeout: float = 30.0
    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 10.0


def safe(config: SafeConfig = None):
    """
    @safe decorator - adds LLM resilience (timeout + retry).
    
    Usage:
        @safe()
        async def my_llm_call():
            return await openai.chat.completions.create(...)
    
    Features:
        - Retry with exponential backoff (3 attempts)
        - Timeout protection (30s default)
        - Graceful error messages
    """
    if config is None:
        config = SafeConfig()
    
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Retry loop with exponential backoff
            for attempt in range(config.max_retries):
                try:
                    # Execute with timeout protection
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=config.timeout
                    )
                    return result
                    
                except asyncio.TimeoutError:
                    if attempt == config.max_retries - 1:
                        return "I'm having trouble processing that request right now. Please try again."
                    
                except Exception:
                    if attempt == config.max_retries - 1:
                        return "Something went wrong while processing your request. Please try again."
                
                # Exponential backoff with jitter (prevents thundering herd)
                if attempt < config.max_retries - 1:
                    delay = min(config.max_delay, config.base_delay * (2 ** attempt))
                    delay *= (0.5 + 0.5 * random.random())  # Add jitter
                    await asyncio.sleep(delay)
            
            return "Unable to process your request after multiple attempts. Please try again later."
        
        return wrapper
    return decorator


