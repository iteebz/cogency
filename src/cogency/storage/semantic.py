"""CANONICAL semantic search - unified abstraction for all similarity operations."""

import json
import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import numpy as np
from resilient_result import Result


class Document:
    """Universal document representation."""
    
    def __init__(self, content: str, metadata: dict = None, similarity: float = 0.0):
        self.content = content
        self.metadata = metadata or {}
        self.similarity = similarity
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "similarity": self.similarity,
        }


class SemanticIndex(ABC):
    """Universal interface for semantic search operations."""
    
    @abstractmethod
    async def search(self, query_embedding: list[float], user_context: str = None, 
                    top_k: int = 5, threshold: float = 0.0) -> list[Document]:
        """Search for semantically similar documents."""
        pass
    
    @abstractmethod
    async def add(self, content: str, metadata: dict, user_context: str = None) -> bool:
        """Add document with auto-embedding."""
        pass


class FileIndex(SemanticIndex):
    """File-based semantic index with JSON persistence."""
    
    def __init__(self, file_path: str, embedder=None):
        self.file_path = Path(file_path)
        self.embedder = embedder
        self._data = None
    
    async def _load_data(self) -> dict:
        """Load embeddings data from file."""
        if self._data is not None:
            return self._data
        
        if not self.file_path.exists():
            # Create empty index
            self._data = {"embeddings": [], "documents": []}
            return self._data
        
        with open(self.file_path) as f:
            data = json.load(f)
        
        # Convert to numpy for efficient computation
        if data.get("embeddings"):
            data["embeddings"] = np.array(data["embeddings"], dtype=np.float32)
        else:
            data["embeddings"] = np.array([], dtype=np.float32).reshape(0, 0)
        
        self._data = data
        return data
    
    async def _save_data(self, data: dict):
        """Save data back to file."""
        # Convert numpy back to lists for JSON
        save_data = data.copy()
        if isinstance(save_data.get("embeddings"), np.ndarray):
            save_data["embeddings"] = save_data["embeddings"].tolist()
        
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        # Update cache
        self._data = data
    
    async def search(self, query_embedding: list[float], user_context: str = None,
                    top_k: int = 5, threshold: float = 0.0) -> list[Document]:
        """Search using cosine similarity."""
        data = await self._load_data()
        
        embeddings = data["embeddings"]
        documents = data["documents"]
        
        if len(embeddings) == 0:
            return []
        
        # Apply user context filter
        if user_context:
            filtered_docs = []
            filtered_embeddings = []
            
            for i, doc in enumerate(documents):
                if doc.get("metadata", {}).get("user_context") == user_context:
                    filtered_docs.append(doc)
                    filtered_embeddings.append(embeddings[i])
            
            if not filtered_docs:
                return []
                
            embeddings = np.array(filtered_embeddings)
            documents = filtered_docs
        
        # Compute cosine similarity
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        # Normalize vectors
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        query_norm = query_vec / np.linalg.norm(query_vec)
        
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Apply threshold
        valid_indices = similarities >= threshold
        valid_similarities = similarities[valid_indices]
        valid_documents = [documents[i] for i, valid in enumerate(valid_indices) if valid]
        
        if len(valid_documents) == 0:
            return []
        
        # Sort by similarity and take top-k
        sorted_indices = np.argsort(valid_similarities)[::-1][:top_k]
        
        results = []
        for idx in sorted_indices:
            doc = Document(
                content=valid_documents[idx]["content"],
                metadata=valid_documents[idx].get("metadata", {}),
                similarity=float(valid_similarities[idx])
            )
            results.append(doc)
        
        return results
    
    async def add(self, content: str, metadata: dict, user_context: str = None) -> bool:
        """Add document with auto-embedding."""
        if not self.embedder:
            raise ValueError("No embedder configured for FileIndex")
        
        # Generate embedding
        embed_result = await self.embedder.embed([content])
        if embed_result.failure:
            return False
        
        embedding = embed_result.data[0]
        
        # Prepare document
        doc_metadata = metadata.copy()
        if user_context:
            doc_metadata["user_context"] = user_context
        
        document = {
            "content": content,
            "metadata": doc_metadata
        }
        
        # Load existing data
        data = await self._load_data()
        
        # Add new embedding and document
        if len(data["embeddings"]) == 0:
            data["embeddings"] = np.array([embedding], dtype=np.float32)
        else:
            data["embeddings"] = np.vstack([data["embeddings"], embedding])
        
        data["documents"].append(document)
        
        # Save
        await self._save_data(data)
        return True


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Pure cosine similarity function."""
    if len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


async def semantic_search(embedder, index: SemanticIndex, query: str, 
                         user_context: str = None, **kwargs) -> Result[list[Document]]:
    """Universal semantic search function."""
    try:
        # Generate query embedding
        embed_result = await embedder.embed([query])
        if embed_result.failure:
            return Result.fail(f"Query embedding failed: {embed_result.error}")
        
        query_embedding = embed_result.data[0]
        
        # Search index
        results = await index.search(query_embedding, user_context, **kwargs)
        
        return Result.ok(results)
    
    except Exception as e:
        return Result.fail(f"Semantic search failed: {str(e)}")