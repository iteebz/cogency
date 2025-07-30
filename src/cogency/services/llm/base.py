"""Base LLM interface - streaming, caching, key rotation, resilience."""

import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Union

from resilient_result import Result, Retry, resilient

from cogency.utils import KeyManager

from .cache import LLMCache

logger = logging.getLogger(__name__)


class LLM(ABC):
    """
    Base class for all LLM implementations in the cogency framework.

    All LLM providers support:
    - Streaming execution for real-time output
    - Automatic key rotation for high-volume usage
    - Rate limiting via yield_interval parameter
    - Unified interface across providers
    - Dynamic model/parameter configuration
    """

    def __init__(
        self,
        provider_name: str,
        api_keys: Union[str, List[str]] = None,
        model: str = None,
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        max_retries: int = 3,
        enable_cache: bool = True,
        **kwargs,
    ):
        # Automatic key management - handles single/multiple keys, rotation, env detection
        self.keys = KeyManager.for_provider(provider_name, api_keys)
        self.provider_name = provider_name
        self.enable_cache = enable_cache

        # Common LLM configuration
        self.model = model or self.default_model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Provider-specific kwargs
        self.extra_kwargs = kwargs

        # Cache instance
        self._cache = LLMCache() if enable_cache else None

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        pass

    def next_key(self) -> str:
        """Get next API key - rotates automatically on every call."""
        return self.keys.get_next()

    @abstractmethod
    def _get_client(self):
        """Get client instance with current API key."""
        pass

    @resilient(retry=Retry.api())
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate a response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the LLM call

        Returns:
            Result containing string response from the LLM or error
        """
        # Check cache first if enabled
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Result.ok(cached_response)

        # Call implementation
        response = await self._run_impl(messages, **kwargs)

        # Cache response if enabled
        if self._cache:
            await self._cache.set(messages, response, **kwargs)

        return Result.ok(response)

    @abstractmethod
    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Internal implementation of LLM call - to be implemented by subclasses."""
        pass

    def _format(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format (standard role/content structure)."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    @resilient(retry=Retry.api())
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            yield_interval: Minimum time between yields for rate limiting (seconds)
            **kwargs: Additional parameters for the LLM call

        Returns:
            AsyncIterator[str] for streaming response
        """
        pass
