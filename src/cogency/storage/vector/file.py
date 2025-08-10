"""File-based vector storage for local embeddings."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from . import VectorStore


class FileStore(VectorStore):
    """Local file-based vector storage.

    Supports JSON format with numpy arrays for embeddings.
    Expected format:
    {
        "embeddings": [[0.1, 0.2, ...], ...],
        "documents": [{"content": "...", "metadata": {...}}, ...]
    }
    """

    def __init__(self, file_path: str):
        """Initialize with path to embeddings file.

        Args:
            file_path: Path to JSON file containing embeddings
        """
        self.file_path = Path(file_path)
        self._data = None

    async def _load_data(self) -> Dict[str, Any]:
        """Load embeddings data from file."""
        if self._data is not None:
            return self._data

        if not self.file_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {self.file_path}")

        with open(self.file_path) as f:
            data = json.load(f)

        # Convert embeddings to numpy arrays for efficient computation
        if "embeddings" in data:
            data["embeddings"] = np.array(data["embeddings"], dtype=np.float32)

        self._data = data
        return data

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using cosine similarity."""
        data = await self._load_data()

        if "embeddings" not in data or "documents" not in data:
            raise ValueError("Invalid embeddings file format")

        embeddings = data["embeddings"]
        documents = data["documents"]

        if len(embeddings) != len(documents):
            raise ValueError("Embeddings and documents length mismatch")

        # Convert query to numpy array
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Compute cosine similarities
        # Normalize vectors
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        query_norm = query_vec / np.linalg.norm(query_vec)

        similarities = np.dot(embeddings_norm, query_norm)

        # Apply threshold filter
        if threshold is not None:
            valid_indices = similarities >= threshold
            similarities = similarities[valid_indices]
            filtered_docs = [documents[i] for i, valid in enumerate(valid_indices) if valid]
        else:
            filtered_docs = documents

        # Apply metadata filters
        if filters:
            filtered_results = []
            filtered_sims = []

            for i, doc in enumerate(filtered_docs):
                metadata = doc.get("metadata", {})
                if self._matches_filters(metadata, filters):
                    filtered_results.append(doc)
                    filtered_sims.append(similarities[i])

            filtered_docs = filtered_results
            similarities = np.array(filtered_sims)

        if len(filtered_docs) == 0:
            return []

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            doc = filtered_docs[idx].copy()
            doc["similarity"] = float(similarities[idx])
            results.append(doc)

        return results

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches all filters."""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    async def add(
        self,
        embeddings: List[List[float]],
        documents: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> bool:
        """Add new embeddings to the file (not implemented for read-only use case)."""
        raise NotImplementedError("FileStore is read-only. Use embedding script to generate files.")

    async def delete(self, ids: List[str]) -> bool:
        """Delete embeddings (not implemented for read-only use case)."""
        raise NotImplementedError("FileStore is read-only. Use embedding script to generate files.")
