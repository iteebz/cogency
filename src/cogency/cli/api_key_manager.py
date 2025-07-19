"""Centralized API key management for all providers."""
from cogency.cli.config import get_api_keys
from cogency.llm.key_rotator import KeyRotator


class ApiKeyManager:
    """Manages API keys and key rotation for all providers."""

    def __init__(self, provider: str):
        self.provider = provider
        self.keys = get_api_keys(provider)
        self.key_rotator = KeyRotator(self.keys) if len(self.keys) > 1 else None

    def get_key(self) -> str:
        """Get the next API key."""
        if self.key_rotator:
            return self.key_rotator.get_key()
        return self.keys[0] if self.keys else None
