from abc import ABC, abstractmethod

import numpy as np


class BaseEmbed(ABC):
    """Base class for embedding providers"""

    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key

    @abstractmethod
    def embed_one(self, text: str, **kwargs) -> np.ndarray:
        """Embed a single text string"""
        pass

    @abstractmethod
    def embed_many(self, texts: list[str], **kwargs) -> list[np.ndarray]:
        """Embed multiple texts"""
        pass

    def embed_array(self, texts: list[str], **kwargs) -> np.ndarray:
        """Embed texts and return as 2D numpy array"""
        embeddings = self.embed_many(texts, **kwargs)
        if not embeddings:
            # Return empty array with correct shape for 2D consistency
            return np.empty((0, self.dimensionality), dtype=np.float32)
        return np.array(embeddings)

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
