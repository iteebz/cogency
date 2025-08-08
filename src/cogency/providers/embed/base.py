"""Base embedding interface - text vectorization with key rotation and resilience."""

from abc import ABC, abstractmethod

import numpy as np
from resilient_result import Result


class Embed(ABC):
    """Base class for embedding providers"""

    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
        self._should_retry = kwargs.get("should_retry", False)
        self.key_rotator = kwargs.get("key_rotator")

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

    @property
    @abstractmethod
    def model(self) -> str:
        """Get the current embedding model"""
        pass

    @property
    @abstractmethod
    def dimensionality(self) -> int:
        """Get the embedding dimensionality"""
        pass
