"""API key rotation for providers."""

import os
import time
from typing import Any, Callable, Optional

# Global client cache: "PROVIDER:api_key" -> client_instance
_client_cache = {}


class Rotator:
    """Generic key rotator that works with any provider."""

    def __init__(self, prefix: str):
        self.prefix = prefix.upper()
        self.keys = self._load_keys()
        self.current = 0
        self.last_rotation = 0

    def _load_keys(self) -> list[str]:
        """Load all numbered keys: PREFIX_API_KEY_1, PREFIX_API_KEY_2, etc."""
        keys = []

        # Load numbered keys
        for i in range(1, 21):
            key = os.environ.get(f"{self.prefix}_API_KEY_{i}")
            if key:
                keys.append(key)

        # Fallback to single key
        single = os.environ.get(f"{self.prefix}_API_KEY")
        if single and single not in keys:
            keys.append(single)

        return keys

    def current_key(self) -> Optional[str]:
        """Get current active key."""
        return self.keys[self.current % len(self.keys)] if self.keys else None

    def rotate(self, error: str = None) -> bool:
        """Rotate if error indicates rate limiting."""
        if not error or len(self.keys) < 2:
            return False

        # Rate limit detection
        rate_signals = ["quota", "rate limit", "429", "throttle", "exceeded"]
        if not any(signal in error.lower() for signal in rate_signals):
            return False

        # Rotate (max once per second)
        now = time.time()
        if now - self.last_rotation > 1:
            self.current = (self.current + 1) % len(self.keys)
            self.last_rotation = now
            return True
        return False


# Global rotators
_rotators: dict[str, Rotator] = {}


async def with_rotation(prefix: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with automatic key rotation on rate limits."""
    if prefix not in _rotators:
        _rotators[prefix] = Rotator(prefix)

    rotator = _rotators[prefix]
    last_error = None

    # Try up to 3 times with different keys
    for _ in range(3):
        key = rotator.current_key()
        if not key:
            raise ValueError(f"No {prefix} API keys found")

        try:
            return await func(key, *args, **kwargs)
        except Exception as e:
            last_error = e
            if not rotator.rotate(str(e)):
                break  # Not a rate limit error or no more keys

    raise last_error


def rotate(func=None, *, prefix: str = None, per_connection: bool = False):
    """Decorator for automatic key rotation with client caching."""
    import inspect

    def decorator(func):
        # Auto-detect prefix from class name if not provided
        def get_prefix(self):
            if prefix:
                return prefix
            return self.__class__.__name__.upper()

        def debug_log(message):
            """Debug logging for rotation events."""
            import os

            if os.getenv("COGENCY_DEBUG_ROTATION"):
                print(f"🔄 ROTATE[{func.__name__}]: {message}")

        # Check if function is async generator
        if inspect.isasyncgenfunction(func):
            # Async generator wrapper with caching
            async def async_gen_wrapper(self, *args, **kwargs):
                provider_prefix = get_prefix(self)

                async def _execute_cached(api_key):
                    # Get cached client
                    cache_key = f"{provider_prefix}:{api_key}"
                    if cache_key not in _client_cache:
                        _client_cache[cache_key] = self._create_client(api_key)
                    client = _client_cache[cache_key]

                    # Call with cached client
                    async for item in func(self, client, *args, **kwargs):
                        yield item

                rotator = _rotators.get(provider_prefix) or Rotator(provider_prefix)
                if provider_prefix not in _rotators:
                    _rotators[provider_prefix] = rotator

                key = rotator.current_key()
                if not key:
                    raise ValueError(f"No {provider_prefix} API keys found")

                try:
                    async for item in _execute_cached(key):
                        yield item
                except Exception as e:
                    if not rotator.rotate(str(e)):
                        raise
                    # Retry with rotated key
                    key = rotator.current_key()
                    async for item in _execute_cached(key):
                        yield item

            return async_gen_wrapper

        # Regular coroutine wrapper with caching
        async def wrapper(self, *args, **kwargs):
            provider_prefix = get_prefix(self)

            async def _execute_cached(api_key):
                # Get cached client
                cache_key = f"{provider_prefix}:{api_key}"
                if cache_key not in _client_cache:
                    _client_cache[cache_key] = self._create_client(api_key)
                client = _client_cache[cache_key]

                # Call with cached client
                return await func(self, client, *args, **kwargs)

            return await with_rotation(provider_prefix, _execute_cached)

        return wrapper

    # Handle both @rotate and @rotate() patterns
    if func is None:
        return decorator
    return decorator(func)
