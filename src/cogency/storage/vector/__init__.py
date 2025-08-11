"""Vector storage interface for semantic search and retrieval.

Provides minimal VectorStore interface for local file storage.

Example:
    ```python
    from cogency.storage.vector import FileStore

    store = FileStore("embeddings.json")
    results = await store.search(query_embedding, top_k=5)
    ```
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class VectorStore(ABC):
    """Universal interface for vector storage backends."""

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict[str, Any]] = None,
        threshold: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector to search with
            top_k: Maximum number of results to return
            filters: Backend-specific metadata filters
            threshold: Minimum similarity threshold

        Returns:
            List of documents with similarity scores and metadata
        """
        pass

    @abstractmethod
    async def add(
        self,
        embeddings: list[list[float]],
        documents: list[dict[str, Any]],
        ids: Optional[list[str]] = None,
    ) -> bool:
        """Add vectors to the store.

        Args:
            embeddings: List of vector embeddings
            documents: List of document metadata/content
            ids: Optional list of document IDs

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def delete(self, ids: list[str]) -> bool:
        """Delete vectors by ID.

        Args:
            ids: List of document IDs to delete

        Returns:
            Success status
        """
        pass


# Import implementations at end to avoid circular dependencies
from .file import FileStore  # noqa: E402

__all__ = [
    "VectorStore",
    "FileStore",
]
