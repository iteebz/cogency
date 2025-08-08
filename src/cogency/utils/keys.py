"""Unified key management for all LLM providers - eliminates DRY violations."""

import itertools
import os
import random
from pathlib import Path
from typing import Awaitable, Callable, List, Optional, TypeVar, Union

from cogency.events import emit
from cogency.utils.heuristics import is_quota_exhausted, is_rate_limit

T = TypeVar("T")

# Auto-load .env file for seamless key detection
try:
    from dotenv import load_dotenv

    # Look for .env file in project root (where cogency is installed)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip auto-loading
    pass


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


class KeyManager:
    """Unified key management - auto-detects, handles rotation, eliminates provider DRY."""

    def __init__(self, api_key: Optional[str] = None, key_rotator: Optional[KeyRotator] = None):
        self.api_key = api_key
        self.key_rotator = key_rotator

    @classmethod
    def for_provider(
        cls, provider: str, api_keys: Optional[Union[str, List[str]]] = None
    ) -> "KeyManager":
        """Factory method - auto-detects keys, handles all scenarios. Replaces 15+ lines of DRY."""
        # Auto-detect from environment if not provided
        if api_keys is None:
            detected_keys = cls.detect_keys(provider)
            if not detected_keys:
                raise ValueError(
                    f"No API keys found for {provider}. Set {provider.upper()}_API_KEY"
                )
            api_keys = detected_keys

        # Handle the key scenarios - unified logic that was duplicated across all providers
        if isinstance(api_keys, list) and len(api_keys) > 1:
            # Multiple keys -> use rotation
            return cls(api_key=None, key_rotator=KeyRotator(api_keys))
        elif isinstance(api_keys, list) and len(api_keys) == 1:
            # Single key in list -> extract it
            return cls(api_key=api_keys[0], key_rotator=None)
        else:
            # Single key as string
            return cls(api_key=api_keys, key_rotator=None)

    @staticmethod
    def detect_keys(provider: str) -> List[str]:
        """Auto-detect API keys from environment variables for any provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'mistral')

        Returns:
            List of detected API keys for the provider

        Example:
            >>> KeyManager.detect_keys('openai')
            ['sk-...', 'sk-...']  # If OPENAI_API_KEY_1, OPENAI_API_KEY_2 are set
        """
        return KeyManager.detect_from_env(provider)

    @staticmethod
    def detect_from_env(provider: str) -> List[str]:
        """Auto-detect API keys from environment variables for any provider.

        Checks for keys in this order:
        1. Numbered keys: PROVIDER_API_KEY_1, PROVIDER_API_KEY_2, etc. (up to 5)
        2. Base key: PROVIDER_API_KEY

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'mistral')

        Returns:
            List of detected API keys for the provider
        """
        keys = []
        env_prefix = provider.upper()

        # Try numbered keys first (PROVIDER_API_KEY_1, PROVIDER_API_KEY_2, etc.)
        # Scan all environment variables to find all numbered keys dynamically
        numbered_keys = []
        for env_var, value in os.environ.items():
            if env_var.startswith(f"{env_prefix}_API_KEY_") and env_var != f"{env_prefix}_API_KEY":
                try:
                    # Extract the number and store with the key
                    suffix = env_var[len(f"{env_prefix}_API_KEY_") :]
                    key_num = int(suffix)
                    numbered_keys.append((key_num, value))
                except ValueError:
                    # Skip non-numeric suffixes
                    continue

        # Sort by key number and add to keys list
        numbered_keys.sort(key=lambda x: x[0])
        keys.extend([key for _, key in numbered_keys])

        # Fall back to base key if no numbered keys found
        if not keys:
            base_key = os.getenv(f"{env_prefix}_API_KEY")
            if base_key:
                keys.append(base_key)

        return keys

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

    async def retry_rate_limit(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
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


__all__ = [
    "KeyManager",
    "KeyRotator",
    "KeyRotationError",
]
