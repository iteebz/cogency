"""Pinecone vector database memory backend."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

try:
    import pinecone
    from pinecone import Pinecone
except ImportError:
    pinecone = None
    Pinecone = None

from .base import BaseMemory, MemoryArtifact, MemoryType, SearchType


class PineconeMemory(BaseMemory):
    """Pinecone vector database memory backend.
    
    Stores memory artifacts in Pinecone with vector embeddings.
    Provides efficient semantic search via Pinecone's vector operations.
    """

    def __init__(
        self, 
        api_key: str,
        index_name: str,
        embedding_provider=None,
        environment: str = "us-east-1-aws",
        dimension: int = 1536
    ):
        """Initialize Pinecone memory backend.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            embedding_provider: Required embedding provider for Pinecone
            environment: Pinecone environment
            dimension: Dimension of embedding vectors
        """
        if Pinecone is None:
            raise ImportError("pinecone-client is required for PineconeMemory. Install with: pip install pinecone-client")
        
        if not embedding_provider:
            raise ValueError("embedding_provider is required for PineconeMemory")
        
        super().__init__(embedding_provider)
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension
        self._client = None
        self._index = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure Pinecone client and index are set up."""
        if self._initialized:
            return
        
        # Initialize Pinecone client
        self._client = Pinecone(api_key=self.api_key)
        
        # Check if index exists, create if not
        existing_indexes = [idx.name for idx in self._client.list_indexes()]
        
        if self.index_name not in existing_indexes:
            # Create index with cosine similarity
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine"
            )
            
            # Wait for index to be ready
            await asyncio.sleep(10)
        
        # Connect to index
        self._index = self._client.Index(self.index_name)
        self._initialized = True

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store content in Pinecone with embedding."""
        await self._ensure_initialized()
        
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding (required for Pinecone)
        embedding = await self.embedding_provider.embed(content)
        if not embedding:
            raise ValueError("Failed to generate embedding for content")
        
        # Prepare metadata for Pinecone (must be JSON serializable)
        pinecone_metadata = {
            "content": content,
            "memory_type": memory_type.value,
            "tags": tags or [],
            "metadata": json.dumps(metadata or {}),
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat()
        }
        
        # Upsert to Pinecone
        self._index.upsert(
            vectors=[(str(artifact.id), embedding, pinecone_metadata)]
        )
        
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
        since: Optional[str] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Search artifacts using Pinecone vector similarity."""
        await self._ensure_initialized()
        
        # Pinecone primarily supports semantic search
        effective_search_type = self._determine_search_type(search_type)
        
        if effective_search_type == SearchType.TEXT:
            # Fallback to semantic search with warning
            effective_search_type = SearchType.SEMANTIC
        
        # Build filter for Pinecone
        pinecone_filter = {}
        
        if memory_type:
            pinecone_filter["memory_type"] = {"$eq": memory_type.value}
        
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        
        if metadata_filter:
            for key, value in metadata_filter.items():
                # Store as JSON string in metadata field
                pinecone_filter["metadata"] = {"$eq": json.dumps({key: value})}
        
        if since:
            pinecone_filter["created_at"] = {"$gte": since}
        
        if effective_search_type == SearchType.SEMANTIC:
            return await self._semantic_search_pinecone(query, pinecone_filter, limit, threshold)
        elif effective_search_type == SearchType.HYBRID:
            # For Pinecone, hybrid is same as semantic with lower threshold
            return await self._semantic_search_pinecone(query, pinecone_filter, limit, threshold * 0.7)
        else:
            return []

    async def _semantic_search_pinecone(self, query: str, filter_dict: Dict, limit: int, threshold: float) -> List[MemoryArtifact]:
        """Perform semantic search using Pinecone."""
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query)
        if not query_embedding:
            return []
        
        # Search in Pinecone
        search_kwargs = {
            "vector": query_embedding,
            "top_k": limit,
            "include_metadata": True
        }
        
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        results = self._index.query(**search_kwargs)
        
        artifacts = []
        for match in results.matches:
            if match.score >= threshold:
                artifact = self._match_to_artifact(match)
                artifact.relevance_score = match.score
                
                # Update access stats
                artifact.access_count += 1
                artifact.last_accessed = datetime.now(UTC)
                await self._update_access_stats_pinecone(artifact)
                
                artifacts.append(artifact)
        
        return artifacts

    async def _update_access_stats_pinecone(self, artifact: MemoryArtifact):
        """Update access statistics for an artifact in Pinecone."""
        # Get current vector data
        fetch_result = self._index.fetch(ids=[str(artifact.id)])
        
        if str(artifact.id) in fetch_result.vectors:
            vector_data = fetch_result.vectors[str(artifact.id)]
            
            # Update metadata
            updated_metadata = vector_data.metadata.copy()
            updated_metadata["access_count"] = artifact.access_count
            updated_metadata["last_accessed"] = artifact.last_accessed.isoformat()
            
            # Upsert with updated metadata
            self._index.upsert(
                vectors=[(str(artifact.id), vector_data.values, updated_metadata)]
            )

    def _match_to_artifact(self, match) -> MemoryArtifact:
        """Convert Pinecone match to MemoryArtifact."""
        metadata = match.metadata
        
        # Parse metadata back from JSON
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
            access_count=metadata.get("access_count", 0),
        )
        
        # Parse datetimes
        if metadata.get("created_at"):
            artifact.created_at = datetime.fromisoformat(metadata["created_at"])
        if metadata.get("last_accessed"):
            artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])
        
        return artifact

    def _determine_search_type(self, search_type: SearchType) -> SearchType:
        """Determine effective search type - Pinecone is primarily semantic."""
        if search_type == SearchType.AUTO:
            return SearchType.SEMANTIC
        elif search_type == SearchType.TEXT:
            # Pinecone doesn't do text search, fallback to semantic
            return SearchType.SEMANTIC
        return search_type

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact from Pinecone."""
        await self._ensure_initialized()
        
        try:
            self._index.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all artifacts from Pinecone."""
        await self._ensure_initialized()
        
        # Pinecone doesn't have a direct "clear all" - delete index and recreate
        try:
            self._client.delete_index(self.index_name)
            await asyncio.sleep(5)  # Wait for deletion
            
            # Recreate index
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine"
            )
            await asyncio.sleep(10)  # Wait for creation
            
            # Reconnect
            self._index = self._client.Index(self.index_name)
        except Exception:
            pass  # Index might not exist

    async def close(self):
        """Clean up Pinecone resources."""
        # Pinecone client doesn't need explicit cleanup
        self._client = None
        self._index = None
        self._initialized = False

    def _get_pinecone_stats(self) -> Dict[str, Any]:
        """Get Pinecone-specific stats."""
        stats = {
            "backend": "pinecone",
            "index_name": self.index_name,
            "environment": self.environment,
            "dimension": self.dimension
        }
        
        if self._index:
            try:
                index_stats = self._index.describe_index_stats()
                stats.update({
                    "total_vector_count": index_stats.total_vector_count,
                    "dimension": index_stats.dimension,
                    "index_fullness": index_stats.index_fullness
                })
            except Exception:
                pass
        
        return stats

    async def inspect(self) -> Dict[str, Any]:
        """Enhanced inspect with Pinecone stats."""
        base_stats = await super().inspect()
        base_stats.update(self._get_pinecone_stats())
        return base_stats