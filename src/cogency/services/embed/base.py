from abc import ABC, abstractmethod

import numpy as np

from cogency.resilience import safe
from cogency.utils.results import Result


class BaseEmbed(ABC):
    """Base class for embedding providers"""

    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key

    @safe.network()
    @abstractmethod
    def embed(self, text: str | list[str], **kwargs) -> Result:
        """Embed text(s) - handles both single strings and lists"""
        pass

    async def embed_text(self, text: str, **kwargs) -> Result:
        """Embed single text - convenience method for memory backends"""
        return self.embed_one(text, **kwargs)

    @safe.network()
    @abstractmethod
    def embed_one(self, text: str, **kwargs) -> Result:
        """Embed a single text string"""
        pass

    @safe.network()
    @abstractmethod
    def embed_many(self, texts: list[str], **kwargs) -> Result:
        """Embed multiple texts"""
        pass

    def embed_array(self, texts: list[str], **kwargs) -> Result:
        """Embed texts and return as 2D numpy array"""
        result = self.embed_many(texts, **kwargs)
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
