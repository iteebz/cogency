"""API key rotation for providers - handles rate limits intelligently."""

import itertools
import random
from typing import Awaitable, Callable, List, Optional, TypeVar

from cogency.events import emit

T = TypeVar("T")


def is_rate_limit(error: Exception) -> bool:
    """Check if error indicates API rate limiting."""
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate limit",
        "too many requests",
        "429",
        "rate_limit_exceeded",
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)


def is_quota_exhausted(error: Exception) -> bool:
    """Check if error indicates quota exhaustion (daily/monthly limits)."""
    error_str = str(error).lower()
    quota_indicators = [
        "quota exceeded",
        "current quota",
        "billing details",
        "resource_exhausted",
        "free tier",
        "exceeded your current quota",
    ]
    return any(indicator in error_str for indicator in quota_indicators)


class KeyRotationError(Exception):
    """Raised when all available API keys have been exhausted due to rate limits."""

    pass


class KeyRotator:
    """Key rotator for API rate limit avoidance."""

    def __init__(self, keys: List[str]):
        self.keys = list(keys)
        # Start with random key
        random.shuffle(self.keys)
        self.cycle = itertools.cycle(self.keys)
        self.current_key: Optional[str] = None
        # Initialize with first key
        self.current_key = next(self.cycle)

    def get_next_key(self) -> str:
        """Get next key in rotation - advances every call."""
        self.current_key = next(self.cycle)
        return self.current_key

    @property
    def current(self) -> str:
        """Get current key without advancing."""
        return self.current_key

    def rotate_key(self) -> str:
        """Rotate to next key immediately. Returns feedback."""
        old_key = self.current_key
        self.get_next_key()
        old_suffix = old_key[-8:] if old_key else "unknown"
        new_suffix = self.current_key[-8:] if self.current_key else "unknown"
        return f"Key *{old_suffix} rate limited, rotating to *{new_suffix}"

    def remove_exhausted_key(self) -> str:
        """Remove current key from rotation when quota exhausted."""
        if len(self.keys) <= 1:
            raise KeyRotationError("Last key exhausted")

        old_suffix = self.current_key[-8:] if self.current_key else "unknown"
        self.keys.remove(self.current_key)
        self.cycle = itertools.cycle(self.keys)
        self.current_key = next(self.cycle)
        return f"Key *{old_suffix} quota exhausted, removed from rotation. {len(self.keys)} keys remaining"


class ApiKeyRotator:
    """API key rotation manager - handles rate limits with intelligent retry."""

    def __init__(self, api_keys: List[str]):
        if not api_keys:
            raise ValueError("ApiKeyRotator requires at least one API key")

        self.api_key = api_keys[0] if len(api_keys) == 1 else None
        self.key_rotator = KeyRotator(api_keys) if len(api_keys) > 1 else None

    @property
    def current(self) -> str:
        """Get the current active key."""
        if self.key_rotator:
            return self.key_rotator.current
        return self.api_key

    def get_next(self) -> str:
        """Get next key in rotation - advances every call."""
        if self.key_rotator:
            return self.key_rotator.get_next_key()
        return self.api_key

    def rotate_key(self) -> Optional[str]:
        """Rotate to next key if rotator exists. Returns feedback message."""
        if self.key_rotator:
            return self.key_rotator.rotate_key()
        return None

    def remove_exhausted_key(self) -> Optional[str]:
        """Remove current exhausted key from rotation. Returns feedback message."""
        if self.key_rotator:
            return self.key_rotator.remove_exhausted_key()
        return None

    def has_multiple(self) -> bool:
        """Check if we have multiple keys available for rotation."""
        return self.key_rotator is not None and len(self.key_rotator.keys) > 1

    async def rotate_retry(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute function with automatic key rotation on rate limits."""
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if not is_rate_limit(e) and not is_quota_exhausted(e):
                    # Not a rate limit or quota error, re-raise original
                    raise

                if not self.has_multiple():
                    # No keys to rotate to, raise policy error
                    emit("error", message=f"Rate limited with no backup keys available: {str(e)}")
                    raise KeyRotationError(
                        f"All API keys exhausted due to rate limits. Original error: {str(e)}"
                    ) from e

                # Handle quota exhaustion vs rate limiting differently
                if is_quota_exhausted(e):
                    removal_msg = self.remove_exhausted_key()
                    emit("debug", message=removal_msg)
                else:
                    rotation_msg = self.rotate_key()
                    emit("debug", message=rotation_msg)

                # Continue loop to retry with new key


__all__ = ["ApiKeyRotator", "KeyRotationError"]
