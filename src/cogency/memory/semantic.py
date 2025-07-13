"""Semantic memory implementation with embedding-based search."""
import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..embed.base import BaseEmbed
from .base import BaseMemory, MemoryArtifact, MemoryType


class SemanticMemory(BaseMemory):
    """Semantic memory backend using embeddings for similarity search.
    
    Extends filesystem storage with embedding-based semantic search capabilities.
    Falls back to text search when embeddings are not available.
    """

    def __init__(
        self, 
        embed_provider: BaseEmbed,
        memory_dir: str = ".cogency_memory",
        similarity_threshold: float = 0.7
    ):
        """Initialize semantic memory.
        
        Args:
            embed_provider: Embedding provider (e.g., NomicEmbed)
            memory_dir: Directory to store memory files
            similarity_threshold: Minimum similarity score for recall results
        """
        self.embed_provider = embed_provider
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.similarity_threshold = similarity_threshold

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryArtifact:
        """Store content with embedding for semantic search."""
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding for semantic search
        try:
            embedding = self.embed_provider.embed_single(content)
            embedding_list = embedding.tolist()  # Convert numpy array to list for JSON
        except Exception as e:
            # Fall back to no embedding if embedding fails
            embedding_list = None
            print(f"Warning: Failed to generate embedding for content: {e}")
        
        # Save artifact with embedding
        file_path = self.memory_dir / f"{artifact.id}.json"
        artifact_data = {
            "id": str(artifact.id),
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at.isoformat(),
            "embedding": embedding_list,
            "embedding_model": self.embed_provider.model if embedding_list else None
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2, ensure_ascii=False)
        
        return artifact

    async def recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None,
        use_semantic: bool = True,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content using semantic similarity or text search."""
        if use_semantic:
            return await self._semantic_recall(query, limit, tags, memory_type, since)
        else:
            return await self._text_recall(query, limit, tags, memory_type, since)

    async def _semantic_recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None
    ) -> List[MemoryArtifact]:
        """Semantic search using embedding similarity."""
        try:
            query_embedding = self.embed_provider.embed_single(query)
        except Exception as e:
            print(f"Warning: Failed to generate query embedding, falling back to text search: {e}")
            return await self._text_recall(query, limit, tags, memory_type, since)
        
        artifacts_with_scores = []
        
        # Load all artifacts and compute similarities
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Skip artifacts without embeddings
                if not data.get("embedding"):
                    continue
                
                # Memory type filtering
                if memory_type:
                    artifact_type = MemoryType(data.get("memory_type", MemoryType.FACT.value))
                    if artifact_type != memory_type:
                        continue
                
                # Tag filtering
                if tags:
                    tag_filter_match = any(tag in data["tags"] for tag in tags)
                    if not tag_filter_match:
                        continue
                
                # Time-based filtering
                if since:
                    from datetime import datetime
                    since_dt = datetime.fromisoformat(since)
                    artifact_dt = datetime.fromisoformat(data["created_at"])
                    if artifact_dt < since_dt:
                        continue
                
                # Compute cosine similarity
                artifact_embedding = np.array(data["embedding"])
                similarity = self._cosine_similarity(query_embedding, artifact_embedding)
                
                # Filter by similarity threshold
                if similarity >= self.similarity_threshold:
                    artifact = self._data_to_artifact(data)
                    artifacts_with_scores.append((artifact, similarity))
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip corrupted files
                continue
        
        # Sort by similarity score (highest first)
        artifacts_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract artifacts and apply limit
        artifacts = [artifact for artifact, _ in artifacts_with_scores]
        if limit:
            artifacts = artifacts[:limit]
        
        return artifacts

    async def _text_recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None
    ) -> List[MemoryArtifact]:
        """Fallback text-based search."""
        artifacts = []
        query_lower = query.lower()
        
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Simple text matching
                content_match = query_lower in data["content"].lower()
                tag_match = any(query_lower in tag.lower() for tag in data["tags"])
                
                # Memory type filtering
                if memory_type:
                    artifact_type = MemoryType(data.get("memory_type", MemoryType.FACT.value))
                    if artifact_type != memory_type:
                        continue
                
                # Tag filtering
                if tags:
                    tag_filter_match = any(tag in data["tags"] for tag in tags)
                    if not tag_filter_match:
                        continue
                
                # Time-based filtering
                if since:
                    from datetime import datetime
                    since_dt = datetime.fromisoformat(since)
                    artifact_dt = datetime.fromisoformat(data["created_at"])
                    if artifact_dt < since_dt:
                        continue
                
                if content_match or tag_match:
                    artifact = self._data_to_artifact(data)
                    artifacts.append(artifact)
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        # Sort by recency
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        
        if limit:
            artifacts = artifacts[:limit]
        
        return artifacts

    def _data_to_artifact(self, data: Dict[str, Any]) -> MemoryArtifact:
        """Convert JSON data back to MemoryArtifact."""
        from datetime import datetime
        
        artifact = MemoryArtifact(
            content=data["content"],
            memory_type=MemoryType(data.get("memory_type", MemoryType.FACT.value)),
            id=UUID(data["id"]),
            tags=data["tags"],
            metadata=data["metadata"]
        )
        artifact.created_at = datetime.fromisoformat(data["created_at"])
        return artifact

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact file."""
        file_path = self.memory_dir / f"{artifact_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def clear(self) -> None:
        """Remove all artifact files."""
        for file_path in self.memory_dir.glob("*.json"):
            file_path.unlink()

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        total_artifacts = 0
        with_embeddings = 0
        embedding_models = set()
        
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                total_artifacts += 1
                if data.get("embedding"):
                    with_embeddings += 1
                    if data.get("embedding_model"):
                        embedding_models.add(data["embedding_model"])
                        
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        return {
            "total_artifacts": total_artifacts,
            "with_embeddings": with_embeddings,
            "embedding_coverage": with_embeddings / total_artifacts if total_artifacts > 0 else 0.0,
            "embedding_models": list(embedding_models),
            "current_model": self.embed_provider.model
        }