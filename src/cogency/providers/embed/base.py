"""Base embedding interface - text vectorization with key rotation and resilience."""

from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np
from resilient_result import Result

from cogency.utils.keys import KeyManager


class Embed(ABC):
    """
    Base class for all embedding implementations in the cogency framework.

    All embedding providers support:
    - Automatic key rotation for high-volume usage
    - Unified interface across providers
    - Dynamic model/parameter configuration
    - Batch processing and dimensionality control
    """

    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = None,  # Must be set by provider
        dimensionality: int = None,  # Must be set by provider
        timeout: float = 15.0,
        max_retries: int = 3,
        **kwargs,
    ):
        # Auto-derive provider name from class name
        provider_name = self.__class__.__name__.lower().replace("embed", "")

        # Automatic key management - handles single/multiple keys, rotation, env detection
        self.keys = KeyManager.for_provider(provider_name, api_keys)
        self.provider_name = provider_name

        # Validate parameters
        if model is None:
            raise ValueError(f"{self.__class__.__name__} must specify a model")
        if dimensionality is None or dimensionality <= 0:
            raise ValueError(f"{self.__class__.__name__} must specify positive dimensionality")
        if not (0 <= timeout <= 300):
            raise ValueError("timeout must be between 0 and 300 seconds")

        # Common embedding configuration
        self.model = model
        self.dimensionality = dimensionality
        self.timeout = timeout
        self.max_retries = max_retries

        # Provider-specific kwargs
        self.extra_kwargs = kwargs

        # Legacy compatibility
        self.api_key = self.keys.current
        self._should_retry = kwargs.get("should_retry", True)
        self.key_rotator = None  # Deprecated - use self.keys

    @abstractmethod
    def embed(self, text: str | list[str], **kwargs) -> Result:
        """Embed text(s) - to be implemented by subclasses"""
        pass

    async def embed_text(self, text: str, **kwargs) -> Result:
        """Embed single text - convenience method for memory stores"""
        return self.embed(text, **kwargs)

    def embed_array(self, texts: list[str], **kwargs) -> Result:
        """Embed texts and return as 2D numpy array"""
        result = self.embed(texts, **kwargs)
        if not result.success:
            return result

        embeddings = result.data
        if not embeddings:
            # Return empty array with correct shape for 2D consistency
            empty_array = np.empty((0, self.dimensionality), dtype=np.float32)
            return Result.ok(empty_array)
        return Result.ok(np.array(embeddings))

    def next_key(self) -> str:
        """Get next API key - rotates automatically on every call."""
        return self.keys.get_next()
