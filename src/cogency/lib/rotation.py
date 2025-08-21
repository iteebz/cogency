"""Zero-ceremony API key rotation for any provider."""

import os
import time
from typing import Any, Callable, Optional


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


def rotated(prefix: str):
    """Decorator for automatic key rotation. ZEALOT APPROVED."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async def _execute(api_key):
                return await func(api_key, *args, **kwargs)

            return await with_rotation(prefix, _execute)

        return wrapper

    return decorator
