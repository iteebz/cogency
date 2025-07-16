"""PGVector storage implementation."""
import json
import asyncio
import numpy as np
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseStorage
from ..base import MemoryArtifact, MemoryType

try:
    import asyncpg
except ImportError:
    asyncpg = None


class PGVectorStorage(BaseStorage):
    """PGVector storage implementation."""
    
    def __init__(
        self, 
        connection_string: str,
        table_name: str = "memory_artifacts",
        vector_dimensions: int = 1536
    ):
        if asyncpg is None:
            raise ImportError("PGVector support not installed. Use `pip install cogency[pgvector]`")
        
        self.connection_string = connection_string
        self.table_name = table_name
        self.vector_dimensions = vector_dimensions
        self._pool = None
        self._initialized = False
    
    async def _ensure_initialized(self):
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
    
    async def store(self, artifact: MemoryArtifact, embedding: Optional[List[float]], **kwargs) -> None:
        await self._ensure_initialized()
        
        embedding_vector = None
        if embedding:
            embedding_vector = f"[{','.join(map(str, embedding))}]"
        
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
    
    async def load_all(self, **filters) -> List[MemoryArtifact]:
        await self._ensure_initialized()
        
        # Build where conditions
        where_conditions = []
        params = []
        param_idx = 1
        
        if filters.get('memory_type'):
            where_conditions.append(f"memory_type = ${param_idx}")
            params.append(filters['memory_type'].value)
            param_idx += 1
        
        if filters.get('tags'):
            where_conditions.append(f"tags && ${param_idx}")
            params.append(filters['tags'])
            param_idx += 1
        
        if filters.get('metadata_filter'):
            for key, value in filters['metadata_filter'].items():
                where_conditions.append(f"metadata->>${param_idx} = ${param_idx + 1}")
                params.extend([key, str(value)])
                param_idx += 2
        
        if filters.get('since'):
            where_conditions.append(f"created_at >= ${param_idx}")
            params.append(filters['since'])
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
        
        return [self._row_to_artifact(row) for row in rows]
    
    async def get_embedding(self, artifact_id: UUID) -> Optional[List[float]]:
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"""
                SELECT embedding FROM {self.table_name} WHERE id = $1
            """, artifact_id)
            
            if row and row['embedding']:
                # Convert PostgreSQL vector to Python list
                vector_str = row['embedding']
                if vector_str.startswith('[') and vector_str.endswith(']'):
                    return [float(x) for x in vector_str[1:-1].split(',')]
        
        return None
    
    async def delete(self, artifact_id: UUID) -> bool:
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(f"""
                DELETE FROM {self.table_name} WHERE id = $1
            """, artifact_id)
            
            return result == "DELETE 1"
    
    async def clear(self) -> None:
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name}")
    
    def _row_to_artifact(self, row) -> MemoryArtifact:
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        artifact = MemoryArtifact(
            id=row['id'],
            content=row['content'],
            memory_type=MemoryType(row['memory_type']),
            tags=list(row['tags']) if row['tags'] else [],
            metadata=metadata,
            confidence_score=float(row['confidence_score']),
            access_count=row['access_count']
        )
        
        artifact.created_at = row['created_at']
        artifact.last_accessed = row['last_accessed']
        
        return artifact