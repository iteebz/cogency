"""PostgreSQL with pgvector extension memory backend."""
import json
import asyncio
import numpy as np
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

try:
    import asyncpg
except ImportError:
    asyncpg = None

from .base import BaseMemory, MemoryArtifact, MemoryType, SearchType
from .filters import filter_artifacts


class PGVectorMemory(BaseMemory):
    """PostgreSQL with pgvector extension memory backend.
    
    Stores memory artifacts in PostgreSQL with vector embeddings using pgvector.
    Provides efficient semantic search via PostgreSQL's vector operations.
    """

    def __init__(
        self, 
        connection_string: str,
        embedding_provider=None,
        table_name: str = "memory_artifacts",
        vector_dimensions: int = 1536
    ):
        """Initialize PGVector memory backend.
        
        Args:
            connection_string: PostgreSQL connection string
            embedding_provider: Optional embedding provider for semantic search
            table_name: Name of the table to store artifacts
            vector_dimensions: Dimension of embedding vectors
        """
        if asyncpg is None:
            raise ImportError("asyncpg is required for PGVectorMemory. Install with: pip install asyncpg")
        
        super().__init__(embedding_provider)
        self.connection_string = connection_string
        self.table_name = table_name
        self.vector_dimensions = vector_dimensions
        self._pool = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database connection and schema are set up."""
        if self._initialized:
            return
        
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.connection_string)
        
        async with self._pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create table with vector column
            await conn.execute(f"""
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
            """)
            
            # Create indexes for efficient search
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                ON {self.table_name} USING ivfflat (embedding vector_cosine_ops);
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_content_idx 
                ON {self.table_name} USING gin(to_tsvector('english', content));
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_tags_idx 
                ON {self.table_name} USING gin(tags);
            """)
        
        self._initialized = True

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store content in PostgreSQL with optional embedding."""
        await self._ensure_initialized()
        
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding if provider available
        embedding_vector = None
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.embed(content)
                if embedding:
                    embedding_vector = f"[{','.join(map(str, embedding))}]"
            except Exception:
                pass  # Graceful degradation
        
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
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
                artifact.last_accessed
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
        """Search artifacts using PostgreSQL with pgvector."""
        await self._ensure_initialized()
        
        # Determine search method
        effective_search_type = self._determine_search_type(search_type)
        
        # Validate search type requirements
        if effective_search_type == SearchType.SEMANTIC and not self.embedding_provider:
            raise ValueError("Semantic search requested but no embedding provider available")
        
        # Build base query with filters
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
        
        if metadata_filter:
            for key, value in metadata_filter.items():
                where_conditions.append(f"metadata->>${param_idx} = ${param_idx + 1}")
                params.extend([key, str(value)])
                param_idx += 2
        
        if since:
            where_conditions.append(f"created_at >= ${param_idx}")
            params.append(since)
            param_idx += 1
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
        
        async with self._pool.acquire() as conn:
            if effective_search_type == SearchType.SEMANTIC:
                return await self._semantic_search_pg(conn, query, where_clause, params, limit, threshold)
            elif effective_search_type == SearchType.TEXT:
                return await self._text_search_pg(conn, query, where_clause, params, limit)
            elif effective_search_type == SearchType.HYBRID:
                return await self._hybrid_search_pg(conn, query, where_clause, params, limit, threshold)
            else:
                return []

    async def _semantic_search_pg(self, conn, query: str, where_clause: str, params: List, limit: int, threshold: float) -> List[MemoryArtifact]:
        """Perform semantic search using pgvector cosine similarity."""
        if not self.embedding_provider:
            return []
        
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query)
        if not query_embedding:
            return []
        
        query_vector = f"[{','.join(map(str, query_embedding))}]"
        
        # Use cosine similarity search
        sql = f"""
            SELECT id, content, memory_type, tags, metadata, created_at, 
                   confidence_score, access_count, last_accessed,
                   1 - (embedding <=> $1::vector) as similarity
            FROM {self.table_name}
            WHERE {where_clause} AND embedding IS NOT NULL
              AND 1 - (embedding <=> $1::vector) >= $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        
        all_params = [query_vector, threshold, limit] + params
        rows = await conn.fetch(sql, *all_params)
        
        artifacts = []
        for row in rows:
            artifact = self._row_to_artifact(row)
            artifact.relevance_score = row['similarity']
            
            # Update access stats
            artifact.access_count += 1
            artifact.last_accessed = datetime.now(UTC)
            await self._update_access_stats(conn, artifact)
            
            artifacts.append(artifact)
        
        return artifacts

    async def _text_search_pg(self, conn, query: str, where_clause: str, params: List, limit: int) -> List[MemoryArtifact]:
        """Perform text search using PostgreSQL full-text search."""
        # Convert query to tsquery format
        query_words = query.lower().split()
        ts_query = " & ".join(query_words) if query_words else query
        
        sql = f"""
            SELECT id, content, memory_type, tags, metadata, created_at,
                   confidence_score, access_count, last_accessed,
                   ts_rank(to_tsvector('english', content), to_tsquery('english', $1)) as rank
            FROM {self.table_name}
            WHERE {where_clause} 
              AND to_tsvector('english', content) @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT $2
        """
        
        all_params = [ts_query, limit] + params
        
        try:
            rows = await conn.fetch(sql, *all_params)
        except Exception:
            # Fallback to simple ILIKE search if tsquery fails
            sql = f"""
                SELECT id, content, memory_type, tags, metadata, created_at,
                       confidence_score, access_count, last_accessed,
                       1.0 as rank
                FROM {self.table_name}
                WHERE {where_clause} AND content ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            all_params = [f"%{query}%", limit] + params
            rows = await conn.fetch(sql, *all_params)
        
        artifacts = []
        for row in rows:
            artifact = self._row_to_artifact(row)
            artifact.relevance_score = float(row['rank'])
            
            # Update access stats
            artifact.access_count += 1
            artifact.last_accessed = datetime.now(UTC)
            await self._update_access_stats(conn, artifact)
            
            artifacts.append(artifact)
        
        return artifacts

    async def _hybrid_search_pg(self, conn, query: str, where_clause: str, params: List, limit: int, threshold: float) -> List[MemoryArtifact]:
        """Perform hybrid search combining semantic and text results."""
        # Get both search results
        semantic_results = await self._semantic_search_pg(conn, query, where_clause, params, limit, threshold * 0.5)
        text_results = await self._text_search_pg(conn, query, where_clause, params, limit)
        
        # Combine and deduplicate
        combined = {}
        
        # Add semantic results with higher weight
        for artifact in semantic_results:
            combined[artifact.id] = artifact
            artifact.relevance_score *= 1.2  # Boost semantic matches
        
        # Add text results
        for artifact in text_results:
            if artifact.id in combined:
                # Combine scores
                combined[artifact.id].relevance_score = (combined[artifact.id].relevance_score + artifact.relevance_score) / 2
            else:
                combined[artifact.id] = artifact
        
        # Sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x.relevance_score * x.decay_score(), reverse=True)
        
        return results[:limit]

    async def _update_access_stats(self, conn, artifact: MemoryArtifact):
        """Update access statistics for an artifact."""
        await conn.execute(f"""
            UPDATE {self.table_name}
            SET access_count = $1, last_accessed = $2
            WHERE id = $3
        """, artifact.access_count, artifact.last_accessed, artifact.id)

    def _row_to_artifact(self, row) -> MemoryArtifact:
        """Convert database row to MemoryArtifact."""
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        artifact = MemoryArtifact(
            id=row['id'],
            content=row['content'],
            memory_type=MemoryType(row['memory_type']),
            tags=list(row['tags']) if row['tags'] else [],
            metadata=metadata,
            confidence_score=float(row['confidence_score']),
            access_count=row['access_count'],
        )
        
        artifact.created_at = row['created_at']
        artifact.last_accessed = row['last_accessed']
        
        return artifact

    def _determine_search_type(self, search_type: SearchType) -> SearchType:
        """Determine effective search type based on availability."""
        if search_type == SearchType.AUTO:
            # Choose semantic if embedding provider available, else text
            return SearchType.SEMANTIC if self.embedding_provider else SearchType.TEXT
        return search_type

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact from PostgreSQL."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(f"""
                DELETE FROM {self.table_name} WHERE id = $1
            """, artifact_id)
            
            return result == "DELETE 1"

    async def clear(self) -> None:
        """Clear all artifacts from PostgreSQL."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name}")

    async def close(self):
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._initialized = False

    def _get_pg_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL-specific stats."""
        return {
            "backend": "pgvector",
            "table_name": self.table_name,
            "vector_dimensions": self.vector_dimensions,
            "connection_string": self.connection_string.split('@')[-1] if '@' in self.connection_string else "localhost"
        }

    async def inspect(self) -> Dict[str, Any]:
        """Enhanced inspect with PostgreSQL stats."""
        base_stats = await super().inspect()
        base_stats.update(self._get_pg_stats())
        
        if self._pool:
            await self._ensure_initialized()
            async with self._pool.acquire() as conn:
                count_result = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
                base_stats["count"] = count_result
                
                # Get table size
                size_result = await conn.fetchval(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{self.table_name}'))
                """)
                base_stats["table_size"] = size_result
        
        return base_stats