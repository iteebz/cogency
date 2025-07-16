"""Pinecone storage implementation."""
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseStorage
from ..base import MemoryArtifact, MemoryType

try:
    import pinecone
    from pinecone import Pinecone
except ImportError:
    pinecone = None
    Pinecone = None


class PineconeStorage(BaseStorage):
    """Pinecone storage implementation."""
    
    def __init__(self, api_key: str, index_name: str, environment: str = "us-east-1-aws", dimension: int = 1536):
        if Pinecone is None:
            raise ImportError("pinecone-client required: pip install pinecone-client")
        
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension
        self._client = None
        self._index = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        if self._initialized:
            return
        
        self._client = Pinecone(api_key=self.api_key)
        
        # Create index if not exists
        existing_indexes = [idx.name for idx in self._client.list_indexes()]
        if self.index_name not in existing_indexes:
            self._client.create_index(name=self.index_name, dimension=self.dimension, metric="cosine")
            await asyncio.sleep(10)  # Wait for index creation
        
        self._index = self._client.Index(self.index_name)
        self._initialized = True
    
    async def store(self, artifact: MemoryArtifact, embedding: Optional[List[float]], **kwargs) -> None:
        await self._ensure_initialized()
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
    
    async def load_all(self, **filters) -> List[MemoryArtifact]:
        await self._ensure_initialized()
        
        # Build Pinecone filter
        pinecone_filter = {}
        if filters.get('memory_type'):
            pinecone_filter["memory_type"] = {"$eq": filters['memory_type'].value}
        if filters.get('tags'):
            pinecone_filter["tags"] = {"$in": filters['tags']}
        if filters.get('since'):
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
    
    async def get_embedding(self, artifact_id: UUID) -> Optional[List[float]]:
        await self._ensure_initialized()
        fetch_result = self._index.fetch(ids=[str(artifact_id)])
        if str(artifact_id) in fetch_result.vectors:
            return fetch_result.vectors[str(artifact_id)].values
        return None
    
    async def delete(self, artifact_id: UUID) -> bool:
        await self._ensure_initialized()
        try:
            self._index.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False
    
    async def clear(self) -> None:
        await self._ensure_initialized()
        try:
            self._client.delete_index(self.index_name)
            await asyncio.sleep(5)
            self._client.create_index(name=self.index_name, dimension=self.dimension, metric="cosine")
            await asyncio.sleep(10)
            self._index = self._client.Index(self.index_name)
        except Exception:
            pass
    
    def _match_to_artifact(self, match) -> MemoryArtifact:
        metadata = match.metadata
        
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
            tags=metadata.get("tags", []),
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=metadata.get("access_count", 0)
        )
        
        if metadata.get("created_at"):
            artifact.created_at = datetime.fromisoformat(metadata["created_at"])
        if metadata.get("last_accessed"):
            artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])
        
        return artifact