"""Pinecone storage implementation."""
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseBackend
from ..core import MemoryArtifact, MemoryType, SearchType

try:
    from pinecone import Pinecone
except (ImportError, Exception):
    # Handle both import errors and package conflicts
    Pinecone = None


class PineconeBackend(BaseBackend):
    """Pinecone storage implementation."""
    
    def __init__(self, api_key: str, index_name: str, environment: str = "us-east-1-aws", dimension: int = 1536, embedding_provider=None):
        if Pinecone is None:
            raise ImportError("Pinecone support not installed. Use `pip install cogency[pinecone]`")
        
        super().__init__(embedding_provider)
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension
        self._client = None
        self._index = None
    
    async def _ensure_ready(self):
        """Initialize Pinecone client and index."""
        if self._index:
            return
        
        self._client = Pinecone(api_key=self.api_key)
        
        # Create index if not exists
        existing_indexes = [idx.name for idx in self._client.list_indexes()]
        if self.index_name not in existing_indexes:
            self._client.create_index(name=self.index_name, dimension=self.dimension, metric="cosine")
            await asyncio.sleep(10)  # Wait for index creation
        
        self._index = self._client.Index(self.index_name)
    
    def _supports_native_search(self, search_type: SearchType) -> bool:
        """Pinecone supports semantic search only."""
        return search_type in [SearchType.SEMANTIC, SearchType.AUTO] and self.embedding_provider
    
    async def _native_search(
        self, query: str, search_type: SearchType, limit: int, threshold: float,
        tags: Optional[List[str]], memory_type: Optional[MemoryType], 
        filters: Optional[Dict[str, Any]], **kwargs
    ) -> List[MemoryArtifact]:
        """Native Pinecone semantic search."""
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Build filter
        pinecone_filter = {}
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        if memory_type:
            pinecone_filter["memory_type"] = {"$eq": memory_type.value}
        if filters:
            for k, v in filters.items():
                pinecone_filter[k] = {"$eq": v}
        
        # Query Pinecone
        query_kwargs = {
            "vector": query_embedding,
            "top_k": limit,
            "include_metadata": True,
            "include_values": False
        }
        
        if pinecone_filter:
            query_kwargs["filter"] = pinecone_filter
            
        results = self._index.query(**query_kwargs)
        
        # Convert to artifacts
        artifacts = []
        for match in results.matches:
            if match.score >= threshold:
                artifact = self._match_to_artifact(match)
                artifact.relevance_score = match.score
                artifacts.append(artifact)
        
        return artifacts
    
    async def _store_artifact(self, artifact: MemoryArtifact, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact in Pinecone."""
        if not embedding:
            raise ValueError("Pinecone requires embeddings")
        
        metadata = {
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": json.dumps(artifact.metadata),
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat()
        }
        
        self._index.upsert(vectors=[(str(artifact.id), embedding, metadata)])
    
    async def _read_by_id(self, artifact_id: UUID) -> List[MemoryArtifact]:
        """Read single artifact by ID."""
        try:
            fetch_result = self._index.fetch(ids=[str(artifact_id)])
            if str(artifact_id) in fetch_result.vectors:
                vector_data = fetch_result.vectors[str(artifact_id)]
                artifact = self._vector_to_artifact(str(artifact_id), vector_data)
                return [artifact]
        except Exception:
            pass
        return []
    
    async def _read_filtered(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Read filtered artifacts."""
        # Build Pinecone filter
        pinecone_filter = {}
        if memory_type:
            pinecone_filter["memory_type"] = {"$eq": memory_type.value}
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        if filters and filters.get('since'):
            pinecone_filter["created_at"] = {"$gte": filters['since']}
        
        # Query with empty vector to get all matching metadata
        query_kwargs = {"vector": [0.0] * self.dimension, "top_k": 10000, "include_metadata": True}
        if pinecone_filter:
            query_kwargs["filter"] = pinecone_filter
        
        results = self._index.query(**query_kwargs)
        
        artifacts = []
        for match in results.matches:
            artifact = self._match_to_artifact(match)
            artifacts.append(artifact)
        
        return artifacts
    
    async def _update_artifact(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact in Pinecone."""
        try:
            # Get existing vector
            fetch_result = self._index.fetch(ids=[str(artifact_id)])
            if str(artifact_id) not in fetch_result.vectors:
                return False
            
            vector_data = fetch_result.vectors[str(artifact_id)]
            current_metadata = vector_data.metadata.copy()
            
            # Apply updates
            for key, value in updates.items():
                if key == 'tags' and isinstance(value, list):
                    current_metadata['tags'] = value
                elif key == 'metadata' and isinstance(value, dict):
                    current_metadata['metadata'] = json.dumps(value)
                elif key in ['access_count', 'confidence_score']:
                    current_metadata[key] = value
                elif key in ['last_accessed']:
                    current_metadata[key] = value.isoformat() if hasattr(value, 'isoformat') else value
            
            # Upsert with updated metadata
            self._index.upsert(vectors=[(str(artifact_id), vector_data.values, current_metadata)])
            return True
        except Exception:
            return False
    
    async def _delete_all(self) -> bool:
        """Delete all artifacts."""
        try:
            self._index.delete(delete_all=True)
            return True
        except Exception:
            return False
    
    async def _delete_by_id(self, artifact_id: UUID) -> bool:
        """Delete single artifact by ID."""
        try:
            self._index.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False
    
    async def _delete_by_filters(self, tags: Optional[List[str]], filters: Optional[Dict[str, Any]]) -> bool:
        """Delete artifacts by filters."""
        pinecone_filter = {}
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        if filters:
            for k, v in filters.items():
                pinecone_filter[k] = {"$eq": v}
        
        try:
            self._index.delete(filter=pinecone_filter)
            return True
        except Exception:
            return False
    
    def _vector_to_artifact(self, vector_id: str, vector_data) -> MemoryArtifact:
        """Convert Pinecone vector data to MemoryArtifact."""
        metadata = vector_data.metadata
        
        # Parse tags (handle both string and list)
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        
        # Parse metadata
        artifact_metadata = {}
        if metadata.get("metadata"):
            try:
                artifact_metadata = json.loads(metadata["metadata"])
            except json.JSONDecodeError:
                pass
        
        artifact = MemoryArtifact(
            id=UUID(vector_id),
            content=metadata["content"],
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0))
        )
        
        if metadata.get("created_at"):
            try:
                artifact.created_at = datetime.fromisoformat(metadata["created_at"])
            except ValueError:
                pass
        
        if metadata.get("last_accessed"):
            try:
                artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])
            except ValueError:
                pass
        
        return artifact
    
    def _match_to_artifact(self, match) -> MemoryArtifact:
        """Convert Pinecone match to MemoryArtifact."""
        metadata = match.metadata
        
        # Parse tags (handle both string and list)
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        
        # Parse metadata
        artifact_metadata = {}
        if metadata.get("metadata"):
            try:
                artifact_metadata = json.loads(metadata["metadata"])
            except json.JSONDecodeError:
                pass
        
        artifact = MemoryArtifact(
            id=UUID(match.id),
            content=metadata["content"],
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0))
        )
        
        if metadata.get("created_at"):
            try:
                artifact.created_at = datetime.fromisoformat(metadata["created_at"])
            except ValueError:
                pass
        
        if metadata.get("last_accessed"):
            try:
                artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])
            except ValueError:
                pass
        
        return artifact
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        def _get_stats():
            stats = self._index.describe_index_stats()
            return {
                'total_memories': stats.total_vector_count,
                'backend': 'pinecone',
                'index_name': self.index_name,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        
        return self._safe_stats(_get_stats, 'pinecone')