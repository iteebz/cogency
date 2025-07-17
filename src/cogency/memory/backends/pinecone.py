"""Pinecone storage implementation."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..core import MemoryBackend, MemoryArtifact, MemoryType, SearchType

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None


class PineconeBackend(MemoryBackend):
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
    
    async def memorize(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MemoryArtifact:
        """Store new content in memory."""
        if not self.embedding_provider:
            raise ValueError("Embedding provider required for Pinecone backend")
            
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Get embedding
        embedding = await self.embedding_provider.embed_text(content)
        
        await self.store(artifact, embedding, **kwargs)
        return artifact
    
    async def recall(
        self,
        query: str,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory."""
        await self._ensure_initialized()
        
        if not self.embedding_provider:
            raise ValueError("Embedding provider required for semantic search")
            
        # Get query embedding
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Build filter
        pinecone_filter = {}
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        if memory_type:
            pinecone_filter["memory_type"] = {"$eq": memory_type.value}
        if metadata_filter:
            for k, v in metadata_filter.items():
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
    
    async def forget(self, artifact_id: UUID = None, tags: Optional[List[str]] = None, metadata_filter: Optional[Dict[str, Any]] = None) -> bool:
        """Remove artifact(s) from memory."""
        await self._ensure_initialized()
        
        if artifact_id:
            return await self.delete(artifact_id)
        
        if tags or metadata_filter:
            # Build filter for deletion
            pinecone_filter = {}
            if tags:
                pinecone_filter["tags"] = {"$in": tags}
            if metadata_filter:
                for k, v in metadata_filter.items():
                    pinecone_filter[k] = {"$eq": v}
            
            try:
                self._index.delete(filter=pinecone_filter)
                return True
            except Exception:
                return False
        
        raise ValueError("Must provide either artifact_id or filters")
    
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
    
    async def clear(self) -> bool:
        await self._ensure_initialized()
        try:
            self._index.delete(delete_all=True)
            return True
        except Exception:
            return False
    
    def _match_to_artifact(self, match) -> MemoryArtifact:
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
        await self._ensure_initialized()
        
        try:
            stats = self._index.describe_index_stats()
            return {
                'total_memories': stats.total_vector_count,
                'backend': 'pinecone',
                'index_name': self.index_name,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        except Exception:
            return {
                'total_memories': 0,
                'backend': 'pinecone',
                'index_name': self.index_name
            }