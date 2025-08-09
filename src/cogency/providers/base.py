"""Unified provider base - LLM and embedding capabilities in single ABC."""

import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Union

from resilient_result import Result

from cogency.utils.keys import KeyManager

from .cache import Cache

logger = logging.getLogger(__name__)


class Provider(ABC):
    """
    Unified provider base - supports LLM and embedding capabilities.

    Providers implement only the capabilities they support:
    - LLM providers: override run() and stream()
    - Embedding providers: override embed()
    - Multi-capability: override all methods

    Unsupported methods raise clear NotImplementedError messages.
    """

    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = None,  # Must be set by provider
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        max_retries: int = 3,
        enable_cache: bool = True,
        cache_ttl: int = 3600,  # 1 hour
        cache_size: int = 1000,  # entries
        **kwargs,
    ):
        # Auto-derive provider name from class name
        provider_name = self.__class__.__name__.lower()

        # Automatic key management
        self.keys = KeyManager.for_provider(provider_name, api_keys)
        self.provider_name = provider_name
        self.enable_cache = enable_cache

        # Validate parameters
        if model is None:
            raise ValueError(f"{self.__class__.__name__} must specify a model")
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        if not (1 <= max_tokens <= 100000):
            raise ValueError("max_tokens must be between 1 and 100000")
        if not (0 <= timeout <= 300):
            raise ValueError("timeout must be between 0 and 300 seconds")

        # Common configuration
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Provider-specific kwargs
        self.extra_kwargs = kwargs

        # Cache instance with configuration
        self._cache = (
            Cache(max_size=cache_size, ttl_seconds=cache_ttl, enable_stats=True)
            if enable_cache
            else None
        )

    def next_key(self) -> str:
        """Get next API key - rotates automatically on every call."""
        return self.keys.get_next()

    @abstractmethod
    def _get_client(self):
        """Get client instance with current API key."""
        pass

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate LLM response - override if provider supports LLM."""
        raise NotImplementedError(f"{self.provider_name} doesn't support LLM")

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response - override if provider supports streaming."""
        raise NotImplementedError(f"{self.provider_name} doesn't support streaming")
        # This never executes, but makes it an async generator
        yield  # pragma: no cover

    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        """Generate embeddings - override if provider supports embeddings."""
        raise NotImplementedError(f"{self.provider_name} doesn't support embeddings")

    def _format(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format (standard role/content structure)."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
