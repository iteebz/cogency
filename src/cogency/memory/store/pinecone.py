"""Pinecone storage implementation."""

import asyncio
import contextlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pinecone import Pinecone as PineconeClient
from resilient_result import Err, Ok, Result

from cogency.memory.store.base import Store
from cogency.memory.types import Memory, MemoryType, SearchType

logger = logging.getLogger(__name__)


class Pinecone(Store):
    """Pinecone storage implementation."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        environment: str = "us-east-1-aws",
        dimension: int = 1536,
        embedder=None,
    ):
        super().__init__(embedder)
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension
        self._client = None
        self._index = None

    async def _ready(self) -> Result[None, Exception]:
        """Initialize Pinecone client and index."""
        if self._index:
            return Ok(None)

        try:
            self._client = PineconeClient(api_key=self.api_key)

            # Create index if not exists
            existing_indexes = [idx.name for idx in self._client.list_indexes()]
            if self.index_name not in existing_indexes:
                self._client.create_index(
                    name=self.index_name, dimension=self.dimension, metric="cosine"
                )
                await asyncio.sleep(10)  # Wait for index creation

            self._index = self._client.Index(self.index_name)
            return Ok(None)
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            return Err(e)

    def _has_search(self, search_type: SearchType) -> bool:
        """Pinecone supports semantic search only."""
        return search_type in [SearchType.SEMANTIC, SearchType.AUTO] and self.embedder

    async def _search(
        self,
        query: str,
        search_type: SearchType,
        limit: int,
        threshold: float,
        tags: Optional[List[str]],
        memory_type: Optional[MemoryType],
        filters: Optional[Dict[str, Any]],
        **kwargs,
    ) -> Result[List[Memory], Exception]:
        """Native Pinecone semantic search."""
        try:
            query_embedding = await self.embedder.embed_text(query)

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
                "include_values": False,
            }

            if pinecone_filter:
                query_kwargs["filter"] = pinecone_filter

            results = self._index.query(**query_kwargs)

            # Convert to artifacts
            artifacts = []
            for match in results.matches:
                if match.score >= threshold:
                    artifact = self._match_to_memory(match)
                    artifact.relevance_score = match.score
                    artifacts.append(artifact)

            return Ok(artifacts)
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return Err(e)

    async def _store(
        self, artifact: Memory, embedding: Optional[List[float]], **kwargs
    ) -> Result[None, Exception]:
        """Store artifact in Pinecone."""
        try:
            if not embedding:
                return Err(ValueError("Pinecone requires embeddings"))

            metadata = {
                "content": artifact.content,
                "memory_type": artifact.memory_type.value,
                "tags": artifact.tags,
                "metadata": json.dumps(artifact.metadata),
                "created_at": artifact.created_at.isoformat(),
                "confidence_score": artifact.confidence_score,
                "access_count": artifact.access_count,
                "last_accessed": artifact.last_accessed.isoformat(),
            }

            self._index.upsert(vectors=[(str(artifact.id), embedding, metadata)])
            return Ok(None)
        except Exception as e:
            logger.error(f"Failed to store artifact in Pinecone: {e}")
            return Err(e)

    async def _read_by_id(self, artifact_id: UUID) -> Result[List[Memory], Exception]:
        """Read single artifact by ID."""
        try:
            fetch_result = self._index.fetch(ids=[str(artifact_id)])
            if str(artifact_id) in fetch_result.vectors:
                vector_data = fetch_result.vectors[str(artifact_id)]
                artifact = self._vector_to_memory(str(artifact_id), vector_data)
                return Ok([artifact])
            return Ok([])
        except Exception as e:
            logger.error(f"Failed to read artifact by ID {artifact_id}: {e}")
            return Err(e)

    async def _read(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result[List[Memory], Exception]:
        """Read filtered artifacts."""
        try:
            # Build Pinecone filter
            pinecone_filter = {}
            if memory_type:
                pinecone_filter["memory_type"] = {"$eq": memory_type.value}
            if tags:
                pinecone_filter["tags"] = {"$in": tags}
            if filters and filters.get("since"):
                pinecone_filter["created_at"] = {"$gte": filters["since"]}

            # Query with empty vector to get all matching metadata
            query_kwargs = {
                "vector": [0.0] * self.dimension,
                "top_k": 10000,
                "include_metadata": True,
            }
            if pinecone_filter:
                query_kwargs["filter"] = pinecone_filter

            results = self._index.query(**query_kwargs)

            artifacts = []
            for match in results.matches:
                artifact = self._match_to_memory(match)
                artifacts.append(artifact)

            return Ok(artifacts)
        except Exception as e:
            logger.error(f"Failed to read filtered artifacts: {e}")
            return Err(e)

    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> Result[bool, Exception]:
        """Update artifact in Pinecone."""
        try:
            # Get existing vector
            fetch_result = self._index.fetch(ids=[str(artifact_id)])
            if str(artifact_id) not in fetch_result.vectors:
                return Ok(False)

            vector_data = fetch_result.vectors[str(artifact_id)]
            current_metadata = vector_data.metadata.copy()

            # Apply updates
            for key, value in updates.items():
                if key == "tags" and isinstance(value, list):
                    current_metadata["tags"] = value
                elif key == "metadata" and isinstance(value, dict):
                    current_metadata["metadata"] = json.dumps(value)
                elif key in ["access_count", "confidence_score"]:
                    current_metadata[key] = value
                elif key in ["last_accessed"]:
                    current_metadata[key] = (
                        value.isoformat() if hasattr(value, "isoformat") else value
                    )

            # Upsert with updated metadata
            self._index.upsert(vectors=[(str(artifact_id), vector_data.values, current_metadata)])
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to update artifact {artifact_id}: {e}")
            return Err(e)

    async def _delete_all(self) -> Result[bool, Exception]:
        """Delete all artifacts."""
        try:
            self._index.delete(delete_all=True)
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to delete all artifacts: {e}")
            return Err(e)

    async def _delete_by_id(self, artifact_id: UUID) -> Result[bool, Exception]:
        """Delete single artifact by ID."""
        try:
            self._index.delete(ids=[str(artifact_id)])
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return Err(e)

    async def _delete_by_filters(
        self,
        tags: Optional[List[str]],
        filters: Optional[Dict[str, Any]],
    ) -> Result[bool, Exception]:
        """Delete artifacts by filters."""
        pinecone_filter = {}
        if tags:
            pinecone_filter["tags"] = {"$in": tags}
        if filters:
            for k, v in filters.items():
                pinecone_filter[k] = {"$eq": v}

        try:
            self._index.delete(filter=pinecone_filter)
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to delete artifacts by filters {pinecone_filter}: {e}")
            return Err(e)

    def _vector_to_memory(self, vector_id: str, vector: Dict) -> Memory:
        """Convert Pinecone vector data to Memory."""
        metadata = vector.metadata

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
            with contextlib.suppress(json.JSONDecodeError):
                artifact_metadata = json.loads(metadata["metadata"])

        artifact = Memory(
            id=UUID(vector_id),
            content=metadata["content"],
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0)),
        )

        if metadata.get("created_at"):
            with contextlib.suppress(ValueError):
                artifact.created_at = datetime.fromisoformat(metadata["created_at"])

        if metadata.get("last_accessed"):
            with contextlib.suppress(ValueError):
                artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])

        return artifact

    def _match_to_memory(self, match) -> Memory:
        """Convert Pinecone match to Memory."""
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
            with contextlib.suppress(json.JSONDecodeError):
                artifact_metadata = json.loads(metadata["metadata"])

        artifact = Memory(
            id=UUID(match.id),
            content=metadata["content"],
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0)),
        )

        if metadata.get("created_at"):
            with contextlib.suppress(ValueError):
                artifact.created_at = datetime.fromisoformat(metadata["created_at"])

        if metadata.get("last_accessed"):
            with contextlib.suppress(ValueError):
                artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])

        return artifact

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""

        def _get_stats():
            stats = self._index.describe_index_stats()
            return {
                "total_memories": stats.total_vector_count,
                "store": "pinecone",
                "index_name": self.index_name,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
            }

        return self._stats(_get_stats, "pinecone")
