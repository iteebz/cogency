"""Unit tests for PGVectorMemory implementation."""

import pytest
from unittest.mock import patch

from cogency.memory.pgvector import PGVectorMemory
from cogency.memory.base import SearchType, MemoryType
from .memory_crud import crud_memorize, crud_recall, crud_forget, crud_clear, assert_artifact


@pytest.fixture
def pgvector_memory(mock_embedding_provider, mock_asyncpg_pool):
    pool, conn = mock_asyncpg_pool
    
    with patch('asyncpg.create_pool', return_value=pool):
        memory = PGVectorMemory(
            connection_string="postgresql://test:test@localhost/test",
            embedding_provider=mock_embedding_provider
        )
        memory.pool = pool
    return memory, conn


@pytest.mark.asyncio
class TestPGVectorMemory:
    
    async def test_memorize(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        await crud_memorize(memory, "test content")
        
        conn.execute.assert_called()
        call_args = conn.execute.call_args[0]
        assert "INSERT INTO memories" in call_args[0]
        assert call_args[1] == "test content"  # content
        assert call_args[4] == "[0.1,0.2,0.3]"  # embedding as JSON
    
    async def test_memorize_no_embedding_fails(self, mock_asyncpg_pool):
        pool, conn = mock_asyncpg_pool
        
        with patch('asyncpg.create_pool', return_value=pool):
            memory = PGVectorMemory(connection_string="postgresql://test:test@localhost/test")
        
        with pytest.raises(ValueError, match="Embedding provider required"):
            await crud_memorize(memory)
    
    async def test_recall(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        mock_rows = [
            {
                'id': 'id-1',
                'content': 'Content 1',
                'memory_type': 'fact',
                'tags': ['test'],
                'metadata': {},
                'created_at': '2024-01-01T00:00:00+00:00',
                'access_count': 0,
                'last_accessed': '2024-01-01T00:00:00+00:00',
                'similarity': 0.9
            },
            {
                'id': 'id-2',
                'content': 'Content 2',
                'memory_type': 'fact',
                'tags': ['test'],
                'metadata': {},
                'created_at': '2024-01-01T00:00:00+00:00',
                'access_count': 0,
                'last_accessed': '2024-01-01T00:00:00+00:00',
                'similarity': 0.8
            }
        ]
        conn.fetch.return_value = mock_rows
        
        results = await crud_recall(memory)
        
        assert len(results) == 2
        assert_artifact(results[0], "Content 1", MemoryType.FACT)
        
        conn.fetch.assert_called()
        query = conn.fetch.call_args[0][0]
        assert "1 - (embedding <=> $1)" in query  # cosine similarity
        assert "LIMIT $2" in query
    
    async def test_recall_with_filters(self, pgvector_memory):
        memory, conn = pgvector_memory
        conn.fetch.return_value = []
        
        await memory.recall(
            query="test",
            tags=["important"],
            memory_type=MemoryType.FACT,
            metadata_filter={"source": "api"}
        )
        
        query = conn.fetch.call_args[0][0]
        assert "$3 = ANY(tags)" in query  # tags filter
        assert "memory_type = $4" in query  # memory_type filter
        assert "metadata->>'source' = $5" in query  # metadata filter
    
    async def test_recall_threshold_filtering(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        mock_rows = [
            {
                'id': 'high-score',
                'content': 'High relevance',
                'memory_type': 'fact',
                'tags': [],
                'metadata': {},
                'created_at': '2024-01-01T00:00:00+00:00',
                'access_count': 0,
                'last_accessed': '2024-01-01T00:00:00+00:00',
                'similarity': 0.9
            },
            {
                'id': 'low-score',
                'content': 'Low relevance',
                'memory_type': 'fact',
                'tags': [],
                'metadata': {},
                'created_at': '2024-01-01T00:00:00+00:00',
                'access_count': 0,
                'last_accessed': '2024-01-01T00:00:00+00:00',
                'similarity': 0.5
            }
        ]
        conn.fetch.return_value = mock_rows
        
        results = await crud_recall(memory, threshold=0.7)
        
        assert len(results) == 1
        assert_artifact(results[0], "High relevance")
    
    async def test_text_search_not_supported(self, pgvector_memory):
        memory, conn = pgvector_memory
        with pytest.raises(NotImplementedError, match="Text search not supported"):
            await memory.recall("test", search_type=SearchType.TEXT)
    
    async def test_hybrid_search_not_supported(self, pgvector_memory):
        memory, conn = pgvector_memory
        with pytest.raises(NotImplementedError, match="Hybrid search not supported"):
            await memory.recall("test", search_type=SearchType.HYBRID)
    
    async def test_forget(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        assert await crud_forget(memory) is True
        
        conn.execute.assert_called()
        query = conn.execute.call_args[0][0]
        assert "DELETE FROM memories WHERE id = $1" in query
        assert conn.execute.call_args[0][1] == "test-id"
    
    async def test_forget_with_filters(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        result = await memory.forget(
            tags=["old"],
            metadata_filter={"source": "deprecated"}
        )
        
        assert result is True
        query = conn.execute.call_args[0][0]
        assert "DELETE FROM memories WHERE" in query
        assert "$1 = ANY(tags)" in query
        assert "metadata->>'source' = $2" in query
    
    async def test_forget_no_criteria_fails(self, pgvector_memory):
        memory, conn = pgvector_memory
        with pytest.raises(ValueError, match="Must provide either artifact_id or filters"):
            await memory.forget()
    
    async def test_clear(self, pgvector_memory):
        memory, conn = pgvector_memory
        
        assert await crud_clear(memory) is True
        
        conn.execute.assert_called()
        query = conn.execute.call_args[0][0]
        assert "DELETE FROM memories" in query
    
    async def test_stats(self, pgvector_memory):
        memory, conn = pgvector_memory
        conn.fetchrow.return_value = {'count': 100}
        
        stats = await memory.get_stats()
        
        assert stats['total_memories'] == 100
        assert stats['backend'] == 'pgvector'