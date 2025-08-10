"""Unified provider base - LLM and embedding capabilities in single ABC."""

import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Union

from resilient_result import Err, Ok, Result

from cogency.providers.rotation import ApiKeyRotator
from cogency.utils.credentials import Credentials

from .cache import Cache


def setup_rotator(
    provider_name: str, api_keys=None, required: bool = True
) -> Optional[ApiKeyRotator]:
    """Beautiful helper - handles credential detection and rotator setup."""
    # Auto-detect if not provided
    if api_keys is None:
        detected = Credentials.detect(provider_name)
        api_keys = detected.get("api_key") if detected else None

    # Set up rotation if we have keys
    if api_keys:
        if isinstance(api_keys, str):
            return ApiKeyRotator([api_keys])
        else:
            return ApiKeyRotator(api_keys)
    elif required:
        raise ValueError(f"{provider_name.title()} requires API keys")
    else:
        return None


logger = logging.getLogger(__name__)


class StreamBuffer:
    """Universal stream retry buffer - handles seamless resumption after failures."""

    def __init__(self, stream_func, rotator=None):
        self.stream_func = stream_func
        self.rotator = rotator
        self.buffer = []
        self.sent_count = 0
        self._exhausted = False

    async def stream_with_retry(self, *args, **kwargs):
        """Stream with automatic retry and seamless resumption."""
        from .rotation import KeyRotationError, is_quota_exhausted, is_rate_limit

        while True:
            try:
                # Start fresh stream and process all chunks
                chunk_index = 0
                async for chunk in self.stream_func(*args, **kwargs):
                    if chunk_index < len(self.buffer):
                        # This chunk was already buffered, verify it matches
                        if chunk != self.buffer[chunk_index]:
                            # Chunks don't match - stream is non-deterministic
                            # This is a limitation we need to handle
                            pass

                        if chunk_index >= self.sent_count:
                            # This buffered chunk hasn't been sent to user yet
                            yield chunk
                            self.sent_count += 1
                    else:
                        # New chunk not in buffer yet
                        self.buffer.append(chunk)
                        yield chunk
                        self.sent_count += 1

                    chunk_index += 1

                # Stream completed successfully
                self._exhausted = True
                break

            except Exception as e:
                if not self.rotator:
                    raise  # No rotator available, re-raise original error

                if not is_rate_limit(e) and not is_quota_exhausted(e):
                    raise  # Not a rate limit error, re-raise original

                if not self.rotator.has_multiple():
                    raise KeyRotationError(
                        f"Stream failed with rate limit and no backup keys available: {str(e)}"
                    ) from e

                # Handle rotation
                if is_quota_exhausted(e):
                    self.rotator.remove_exhausted_key()
                else:
                    self.rotator.rotate_key()

                # Continue loop to retry - stream will restart but we only yield unsent chunks


def rotate_retry(func):
    """Beautiful decorator - automatic key rotation on rate limits."""
    from functools import wraps

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if hasattr(self, "rotator") and self.rotator:
            try:
                result = await self.rotator.rotate_retry(func, self, *args, **kwargs)
                return result if isinstance(result, Result) else Ok(result)
            except Exception as e:
                return Err(e)
        else:
            # No rotator - call method directly
            try:
                result = await func(self, *args, **kwargs)
                return result if isinstance(result, Result) else Ok(result)
            except Exception as e:
                return Err(e)

    # Mark this as our rotate_retry decorator
    wrapper._is_rotate_retry = True
    return wrapper


def stream_retry(func):
    """Beautiful decorator - automatic stream retry with seamless resumption."""
    from functools import wraps

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        rotator = getattr(self, "rotator", None)
        buffer = StreamBuffer(func, rotator)

        async for chunk in buffer.stream_with_retry(self, *args, **kwargs):
            yield chunk

    # Mark this as our stream_retry decorator
    wrapper._is_stream_retry = True
    return wrapper


class Provider(ABC):
    """
    Unified provider base - supports LLM and embedding capabilities.

    Providers implement only the capabilities they support:
    - LLM providers: override run() and stream()
    - Embedding providers: override embed()
    - Multi-capability: override all methods

    Key rotation is automatically applied to all provider methods.
    """

    def __init_subclass__(cls, **kwargs):
        """Automatically wrap provider methods with key rotation."""
        super().__init_subclass__(**kwargs)

        # Apply decorators to provider methods based on their return types
        method_decorators = {
            "run": (rotate_retry, "_is_rotate_retry"),
            "embed": (rotate_retry, "_is_rotate_retry"),
            "stream": (stream_retry, "_is_stream_retry"),
        }

        for method_name, (decorator, marker_attr) in method_decorators.items():
            if method_name in cls.__dict__:
                provider_method = cls.__dict__[method_name]
                # Only wrap if not manually decorated already
                if not getattr(provider_method, marker_attr, False):
                    wrapped_method = decorator(provider_method)
                    setattr(cls, method_name, wrapped_method)

    def __init__(
        self,
        rotator: Optional[ApiKeyRotator] = None,
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
        self.provider_name = self.__class__.__name__.lower()
        self.enable_cache = enable_cache

        # Simple rotator assignment - providers handle their own credential logic
        self.rotator = rotator

        # Backward compatibility - expose current key if rotator exists
        self.api_key = rotator.current if rotator else None

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
        if self.rotator:
            return self.rotator.get_next()
        return self.api_key

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
