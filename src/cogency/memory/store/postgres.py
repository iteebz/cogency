"""PGVector storage implementation."""

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from resilient_result import Err, Ok, Result

from cogency.memory.store.base import Store
from cogency.memory.types import Memory, MemoryType, SearchType

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_DIMENSION = 1536
DEFAULT_CONFIDENCE_SCORE = 1.0
DEFAULT_ACCESS_COUNT = 0

try:
    import asyncpg
except ImportError:
    asyncpg = None


class PGVector(Store):
    """PGVector storage implementation."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "memory_artifacts",
        vector_dimensions: int = DEFAULT_EMBEDDING_DIMENSION,
        embedder=None,
    ):
        if asyncpg is None:
            raise ImportError(
                "PGVector support not installed. Use `pip install cogency[pgvector]`"
            ) from None

        super().__init__(embedder)
        self.connection_string = connection_string
        self.table_name = table_name
        self.vector_dimensions = vector_dimensions
        self._pool = None

    async def _ready(self) -> Result[None, Exception]:
        """Initialize PGVector database and table."""
        if self._pool:
            return Ok(None)

        try:
            self._pool = await asyncpg.create_pool(self.connection_string)

            async with self._pool.acquire() as conn:
                # Enable pgvector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Create table with vector column
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id UUID PRIMARY KEY,
                        content TEXT NOT NULL,
                        memory_type VARCHAR(50) NOT NULL,
                        tags TEXT[] DEFAULT '{{}}',
                        metadata JSONB DEFAULT '{{}}',
                        embedding vector({self.vector_dimensions}),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        confidence_score REAL DEFAULT 1.0,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """
                )

                # Create indexes for efficient search
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                    ON {self.table_name} USING ivfflat (embedding vector_cosine_ops);
                """
                )
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_content_idx
                    ON {self.table_name} USING gin(to_tsvector('english', content));
                """
                )
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_tags_idx
                    ON {self.table_name} USING gin(tags);
                """
                )
            return Ok(None)
        except Exception as e:
            logger.error(f"Failed to initialize PGVector: {e}")
            return Err(e)

    def _has_search(self, search_type: SearchType) -> bool:
        """PGVector supports semantic search when embeddings available."""
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
        """Native PGVector semantic search."""
        try:
            query_embedding = await self.embedder.embed_text(query)
            vector_search_result = await self._vector_search(query_embedding, limit, threshold)
            if vector_search_result.failure:
                return Err(vector_search_result.error)
            return Ok(vector_search_result.data)
        except Exception as e:
            logger.error(f"Failed to search PGVector: {e}")
            return Err(e)

    async def _store(
        self, artifact: Memory, embedding: Optional[List[float]], **kwargs
    ) -> Result[None, Exception]:
        """Store artifact in PGVector."""
        try:
            embedding_vector = None
            if embedding:
                embedding_vector = f"[{','.join(map(str, embedding))}]"

            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.table_name}
                    (id, content, memory_type, tags, metadata, embedding, created_at,
                     confidence_score, access_count, last_accessed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    artifact.id,
                    artifact.content,
                    artifact.memory_type.value,
                    artifact.tags,
                    json.dumps(artifact.metadata),
                    embedding_vector,
                    artifact.created_at,
                    artifact.confidence_score,
                    artifact.access_count,
                    artifact.last_accessed,
                )
            return Ok(None)
        except Exception as e:
            logger.error(f"Failed to store artifact in PGVector: {e}")
            return Err(e)

    async def _read_by_id(self, artifact_id: UUID) -> Result[List[Memory], Exception]:
        """Read single artifact by ID."""
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT id, content, memory_type, tags, metadata, created_at,
                           confidence_score, access_count, last_accessed
                    FROM {self.table_name}
                    WHERE id = $1
                """,
                    artifact_id,
                )

                if row:
                    return Ok([self._row_to_memory(row)])
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
            # Build where conditions
            where_conditions = []
            params = []
            param_idx = 1

            if memory_type:
                where_conditions.append(f"memory_type = ${param_idx}")
                params.append(memory_type.value)
                param_idx += 1

            if tags:
                where_conditions.append(f"tags && ${param_idx}")
                params.append(tags)
                param_idx += 1

            if filters:
                if filters.get("metadata_filter"):
                    for key, value in filters["metadata_filter"].items():
                        where_conditions.append(f"metadata->>${param_idx} = ${param_idx + 1}")
                        params.extend([key, str(value)])
                        param_idx += 2

                if filters.get("since"):
                    where_conditions.append(f"created_at >= ${param_idx}")
                    params.append(filters["since"])
                    param_idx += 1

            where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

            sql = f"""
                SELECT id, content, memory_type, tags, metadata, created_at,
                       confidence_score, access_count, last_accessed
                FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY created_at DESC
            """

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)

            return Ok([self._row_to_memory(row) for row in rows])
        except Exception as e:
            logger.error(f"Failed to read filtered artifacts: {e}")
            return Err(e)

    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> Result[bool, Exception]:
        """Update artifact in PGVector."""
        try:
            # Build update query dynamically
            set_clauses = []
            params = []
            param_idx = 1

            for key, value in updates.items():
                if key == "tags" and isinstance(value, list):
                    set_clauses.append(f"tags = ${param_idx}")
                    params.append(value)
                elif key == "metadata" and isinstance(value, dict):
                    set_clauses.append(f"metadata = ${param_idx}")
                    params.append(json.dumps(value))
                elif key in ["access_count", "confidence_score"] or key in ["last_accessed"]:
                    set_clauses.append(f"{key} = ${param_idx}")
                    params.append(value)
                param_idx += 1

            if not set_clauses:
                return Ok(True)

            params.append(artifact_id)
            sql = f"""
                UPDATE {self.table_name}
                SET {", ".join(set_clauses)}
                WHERE id = ${param_idx}
            """

            async with self._pool.acquire() as conn:
                result = await conn.execute(sql, *params)
                return Ok(result == "UPDATE 1")
        except Exception as e:
            logger.error(f"Failed to update artifact {artifact_id}: {e}")
            return Err(e)

    async def _delete_all(self) -> Result[bool, Exception]:
        """Delete all artifacts."""
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(f"TRUNCATE TABLE {self.table_name}")
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to delete all artifacts: {e}")
            return Err(e)

    async def _delete_by_id(self, artifact_id: UUID) -> Result[bool, Exception]:
        """Delete single artifact by ID."""
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    f"""
                    DELETE FROM {self.table_name} WHERE id = $1
                """,
                    artifact_id,
                )
                return Ok(result == "DELETE 1")
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return Err(e)

    async def _delete_by_filters(
        self,
        tags: Optional[List[str]],
        filters: Optional[Dict[str, Any]],
    ) -> Result[bool, Exception]:
        """Delete artifacts by filters."""
        try:
            where_conditions = []
            params = []
            param_idx = 1

            if tags:
                where_conditions.append(f"tags && ${param_idx}")
                params.append(tags)
                param_idx += 1

            if filters:
                for key, value in filters.items():
                    if key != "user_id":
                        where_conditions.append(f"metadata->>${param_idx} = ${param_idx + 1}")
                        params.extend([key, str(value)])
                        param_idx += 2

            if where_conditions:
                where_clause = " AND ".join(where_conditions)
                sql = f"DELETE FROM {self.table_name} WHERE {where_clause}"

                async with self._pool.acquire() as conn:
                    await conn.execute(sql, *params)
                return Ok(True)
            return Ok(False)  # No conditions, nothing to delete
        except Exception as e:
            logger.error(f"Failed to delete artifacts by filters: {e}")
            return Err(e)

    async def _vector_search(
        self,
        query_embedding: List[float],
        limit: int,
        threshold: float,
    ) -> Result[List[Memory], Exception]:
        """Perform vector similarity search using PGVector."""
        try:
            embedding_vector = f"[{','.join(map(str, query_embedding))}]"

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT id, content, memory_type, tags, metadata, created_at,
                           confidence_score, access_count, last_accessed,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM {self.table_name}
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> $1::vector) >= $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                """,
                    embedding_vector,
                    threshold,
                    limit,
                )

            results = []
            for row in rows:
                artifact = self._row_to_memory(row)
                artifact.relevance_score = float(row["similarity"])
                results.append(artifact)

            return Ok(results)
        except Exception as e:
            logger.error(f"Failed to perform vector search: {e}")
            return Err(e)

    def _row_to_memory(self, row: Dict) -> Memory:
        """Convert database row to Memory."""
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        artifact = Memory(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            tags=list(row["tags"]) if row["tags"] else [],
            metadata=metadata,
            confidence_score=float(row["confidence_score"]),
            access_count=row["access_count"],
        )

        artifact.created_at = row["created_at"]
        artifact.last_accessed = row["last_accessed"]

        return artifact

    async def get_stats(self) -> Result[Dict[str, Any], Exception]:
        """Get memory statistics."""

        async def _get_stats() -> Dict[str, Any]:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(f"SELECT COUNT(*) as count FROM {self.table_name}")
                return {
                    "total_memories": row["count"],
                    "store": "pgvector",
                    "table_name": self.table_name,
                }

        try:
            stats = await _get_stats()
            return Ok(stats)
        except Exception as e:
            logger.error(f"Failed to get PGVector stats: {e}")
            return Err(e)
