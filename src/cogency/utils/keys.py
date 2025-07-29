"""Unified key management for all LLM providers - eliminates DRY violations."""

import itertools
import os
import random
from pathlib import Path
from typing import List, Optional, Union

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


class KeyRotator:
    """Simple key rotator for API rate limit avoidance."""

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

    def get_current_key(self) -> str:
        """Get current key without advancing."""
        return self.current_key

    def rotate_key(self) -> str:
        """Rotate to next key immediately. Returns feedback."""
        old_key = self.current_key
        self.get_next_key()
        old_suffix = old_key[-8:] if old_key else "unknown"
        new_suffix = self.current_key[-8:] if self.current_key else "unknown"
        return f"Key *{old_suffix} rate limited, rotating to *{new_suffix}"


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
            detected_keys = cls._detect_keys_from_env(provider)
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
    def _detect_keys_from_env(provider: str) -> List[str]:
        """Auto-detect API keys from environment variables for any provider."""
        keys = []
        env_prefix = provider.upper()

        # Try numbered keys first (PROVIDER_API_KEY_1, PROVIDER_API_KEY_2, etc.)
        for i in range(1, 6):  # Check up to 5 numbered keys
            key = os.getenv(f"{env_prefix}_API_KEY_{i}")
            if key:
                keys.append(key)

        # Fall back to base key if no numbered keys found
        if not keys:
            base_key = os.getenv(f"{env_prefix}_API_KEY")
            if base_key:
                keys.append(base_key)

        return keys

    def get_current(self) -> str:
        """Get the current active key."""
        if self.key_rotator:
            return self.key_rotator.get_current_key()
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

    def has_multiple(self) -> bool:
        """Check if we have multiple keys available for rotation."""
        return self.key_rotator is not None
