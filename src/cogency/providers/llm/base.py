"""Base LLM interface - streaming, caching, key rotation, resilience."""

import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Union

from resilient_result import Result

from cogency.events import emit
from cogency.utils.keys import KeyManager

from .cache import LLMCache


# Simple token counting for cost tracking
def count_tokens(text: str) -> int:
    """Simple token count approximation."""
    return len(text.split()) * 1.3  # Rough approximation


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Simple cost calculation."""
    return (input_tokens + output_tokens) * 0.00001  # Rough approximation


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

        # Automatic key management - handles single/multiple keys, rotation, env detection
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

        # Common LLM configuration
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Provider-specific kwargs
        self.extra_kwargs = kwargs

        # Cache instance with configuration
        self._cache = (
            LLMCache(max_size=cache_size, ttl_seconds=cache_ttl, enable_stats=True)
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
        """Generate a response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the LLM call

        Returns:
            Result containing string response from the LLM or error
        """
        from cogency.events import emit

        emit(
            "llm",
            level="debug",
            operation="run",
            provider=self.provider_name,
            model=self.model,
            status="start",
        )

        try:
            result = await self._run_with_metrics(messages, **kwargs)

            emit(
                "llm",
                operation="run",
                provider=self.provider_name,
                model=self.model,
                status="complete",
                success=result.success,
            )

            return result

        except Exception as e:
            emit(
                "llm",
                operation="run",
                provider=self.provider_name,
                model=self.model,
                status="error",
                error=str(e),
            )
            emit("trace", message=f"LLM {self.provider_name} failed: {str(e)}")
            logger.debug(f"LLM {self.provider_name} failed: {e}")
            raise

    async def _run_with_metrics(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Run implementation with metrics and caching"""
        # Count input tokens
        message_text = " ".join([msg.get("content", "") for msg in messages])
        tin = int(count_tokens(message_text))

        # Check cache first if enabled
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Result.ok(cached_response)

        # Call implementation with rate limit retry
        response = await self.keys.retry_rate_limit(self._run_impl, messages, **kwargs)

        # Count output tokens and track cost
        tout = int(count_tokens(response))
        total_cost = calculate_cost(tin, tout, self.model)

        # Emit beautiful notification
        emit(
            "tokens",
            tin=tin,
            tout=tout,
            cost=f"${total_cost:.4f}",
            provider=self.provider_name,
            model=self.model,
        )

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

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            yield_interval: Minimum time between yields for rate limiting (seconds)
            **kwargs: Additional parameters for the LLM call

        Returns:
            AsyncIterator[str] for streaming response
        """
        # Note: Streaming doesn't support retry currently due to complexity of async generator retry
        # When robust=False, this behavior is maintained (no retries for streaming)
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk

    @abstractmethod
    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Internal stream implementation - to be implemented by subclasses"""
        pass
