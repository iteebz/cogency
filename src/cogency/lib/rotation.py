"""API key rotation for providers."""

import os
import time
from collections.abc import Callable
from typing import Any

# No client caching - WebSocket clients hold stateful connections


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

    def current_key(self) -> str | None:
        """Get current active key."""
        return self.keys[self.current % len(self.keys)] if self.keys else None

    def rotate(self, error: str = None) -> bool:
        """Rotate on rate limits or force rotation."""
        if len(self.keys) < 2:
            return False

        # Force rotation if no error (proactive load balancing)
        if not error:
            # Always rotate for load balancing - remove time restriction
            self.current = (self.current + 1) % len(self.keys)
            self.last_rotation = time.time()
            return True

        # Rate limit detection
        rate_signals = ["quota", "rate limit", "429", "throttle", "exceeded"]
        rate_detected = any(signal in error.lower() for signal in rate_signals)

        if not rate_detected:
            return False

        # Always rotate on rate limit errors - no time restriction
        self.current = (self.current + 1) % len(self.keys)
        self.last_rotation = time.time()
        return True


# Global rotators
_rotators: dict[str, Rotator] = {}


async def with_rotation(prefix: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with automatic key rotation (rotate every call + retry on failure)."""
    if prefix not in _rotators:
        _rotators[prefix] = Rotator(prefix)

    rotator = _rotators[prefix]

    # Step 1: Automatically rotate to next key for load balancing
    rotator.rotate()  # Force rotation (no error = proactive rotation)

    key = rotator.current_key()
    if not key:
        raise RuntimeError(f"No {prefix} API keys found")

    # Step 2: Try the call with current key
    try:
        return await func(key, *args, **kwargs)
    except Exception as e:
        # Step 3: If failure, rotate again and retry once
        rotated = rotator.rotate(str(e))
        if not rotated:
            raise e  # Not a rate limit or no more keys, preserve original error

        # Retry with different key
        retry_key = rotator.current_key()
        if not retry_key:
            raise RuntimeError(f"No {prefix} API keys available for retry") from None

        try:
            return await func(retry_key, *args, **kwargs)
        except Exception as retry_error:
            raise retry_error


def rotate(func=None, *, prefix: str = None, per_connection: bool = False):
    """Decorator for automatic key rotation with fresh clients."""
    import inspect

    def decorator(func):
        # Auto-detect prefix from class name if not provided
        def get_prefix(self):
            if prefix:
                return prefix
            return self.__class__.__name__.upper()

        # Check if function is async generator
        if inspect.isasyncgenfunction(func):
            # Async generator wrapper
            async def async_gen_wrapper(self, *args, **kwargs):
                provider_prefix = get_prefix(self)

                async def _execute(api_key):
                    # Create fresh client for each call
                    client = self._create_client(api_key)

                    # Call with fresh client
                    async for item in func(self, client, *args, **kwargs):
                        yield item

                rotator = _rotators.get(provider_prefix) or Rotator(provider_prefix)
                if provider_prefix not in _rotators:
                    _rotators[provider_prefix] = rotator

                # Check for API keys first - fail fast on config errors
                if not rotator.keys:
                    raise RuntimeError(f"No {provider_prefix} API keys found")

                # Step 1: Auto-rotate for load balancing
                rotator.rotate()
                key = rotator.current_key()

                try:
                    async for item in _execute(key):
                        yield item
                except Exception as e:
                    # Step 2: If failure, rotate again and retry once
                    if not rotator.rotate(str(e)):
                        raise e

                    key = rotator.current_key()
                    if not key:  # Safety check after rotation
                        raise RuntimeError(
                            f"No {provider_prefix} API keys available for retry"
                        ) from None

                    try:
                        async for item in _execute(key):
                            yield item
                    except Exception as retry_error:
                        raise retry_error

            return async_gen_wrapper

        # Regular coroutine wrapper
        async def wrapper(self, *args, **kwargs):
            provider_prefix = get_prefix(self)

            async def _execute(api_key):
                # Create fresh client for each call
                client = self._create_client(api_key)

                # Call with fresh client
                return await func(self, client, *args, **kwargs)

            # with_rotation now handles auto-rotation + retry automatically
            return await with_rotation(provider_prefix, _execute)

        return wrapper

    # Handle both @rotate and @rotate() patterns
    if func is None:
        return decorator
    return decorator(func)
