"""Tests for PGVector memory backend."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from cogency.memory.base import MemoryType, SearchType


class TestPGVectorMemory:
    """Test PGVector memory backend with mocked dependencies."""
    
    @pytest.fixture
    def mock_embedding_provider(self):
        """Mock embedding provider."""
        provider = Mock()
        provider.embed = AsyncMock()
        provider.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return provider
    
    @pytest.fixture
    def mock_asyncpg_pool(self):
        """Mock asyncpg connection pool."""
        pool = Mock()
        conn = Mock()
        
        # Mock connection context manager
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)
        conn.execute = AsyncMock()
        conn.fetch = AsyncMock(return_value=[])
        conn.fetchval = AsyncMock(return_value=0)
        
        pool.acquire.return_value = conn
        
        return pool, conn
    
    @pytest.fixture
    def pgvector_memory(self, mock_embedding_provider, mock_asyncpg_pool):
        """PGVector memory instance with mocked dependencies."""
        with patch('cogency.memory.pgvector.asyncpg') as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_asyncpg_pool[0])
            
            from cogency.memory.pgvector import PGVectorMemory
            memory = PGVectorMemory(
                connection_string="postgresql://user:pass@localhost/test",
                embedding_provider=mock_embedding_provider
            )
            memory._pool = mock_asyncpg_pool[0]
            memory._initialized = True
            
            return memory, mock_asyncpg_pool[1]
    
    @pytest.mark.asyncio
    async def test_import_error_without_asyncpg(self):
        """Test that ImportError is raised when asyncpg is not available."""
        with patch('cogency.memory.pgvector.asyncpg', None):
            with pytest.raises(ImportError, match="asyncpg is required"):
                from cogency.memory.pgvector import PGVectorMemory
                PGVectorMemory("postgresql://test")
    
    @pytest.mark.asyncio
    async def test_memorize_with_embedding(self, pgvector_memory, mock_embedding_provider):
        """Test memorizing content with embedding generation."""
        memory, mock_conn = pgvector_memory
        
        content = "Test content for memorization"
        artifact = await memory.memorize(content, tags=["test"])
        
        assert artifact.content == content
        assert artifact.tags == ["test"]
        assert artifact.memory_type == MemoryType.FACT
        
        # Verify embedding was generated
        mock_embedding_provider.embed.assert_called_once_with(content)
        
        # Verify database insert was called
        mock_conn.execute.assert_called_once()
        insert_call = mock_conn.execute.call_args[0]
        assert "INSERT INTO" in insert_call[0]
        assert artifact.id in insert_call[1:]
    
    @pytest.mark.asyncio
    async def test_memorize_without_embedding_provider(self, mock_asyncpg_pool):
        """Test memorizing content without embedding provider."""
        with patch('cogency.memory.pgvector.asyncpg') as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_asyncpg_pool[0])
            
            from cogency.memory.pgvector import PGVectorMemory
            memory = PGVectorMemory("postgresql://test")
            memory._pool = mock_asyncpg_pool[0]
            memory._initialized = True
            
            _, mock_conn = mock_asyncpg_pool
            
            artifact = await memory.memorize("Test content")
            
            assert artifact.content == "Test content"
            
            # Verify database insert was called with None embedding
            mock_conn.execute.assert_called_once()
            insert_call = mock_conn.execute.call_args[0]
            assert None in insert_call[1:]  # embedding should be None
    
    @pytest.mark.asyncio
    async def test_semantic_search_success(self, pgvector_memory, mock_embedding_provider):
        """Test semantic search with successful results."""
        memory, mock_conn = pgvector_memory
        
        # Mock database response
        mock_row = {
            'id': uuid4(),
            'content': 'Test content',
            'memory_type': 'fact',
            'tags': ['test'],
            'metadata': '{}',
            'created_at': '2024-01-01T00:00:00+00:00',
            'confidence_score': 1.0,
            'access_count': 0,
            'last_accessed': '2024-01-01T00:00:00+00:00',
            'similarity': 0.85
        }
        mock_conn.fetch.return_value = [mock_row]
        
        results = await memory.recall("test query", search_type=SearchType.SEMANTIC, threshold=0.8)
        
        assert len(results) == 1
        assert results[0].content == "Test content"
        assert results[0].relevance_score == 0.85
        
        # Verify embedding was generated for query
        mock_embedding_provider.embed.assert_called_with("test query")
        
        # Verify semantic search SQL was used
        mock_conn.fetch.assert_called_once()
        search_call = mock_conn.fetch.call_args[0]
        assert "vector" in search_call[0].lower()
        assert "cosine" in search_call[0].lower()
    
    @pytest.mark.asyncio
    async def test_text_search_success(self, pgvector_memory):
        """Test text search with successful results."""
        memory, mock_conn = pgvector_memory
        
        # Mock database response
        mock_row = {
            'id': uuid4(),
            'content': 'Test content with keywords',
            'memory_type': 'fact',
            'tags': ['test'],
            'metadata': '{}',
            'created_at': '2024-01-01T00:00:00+00:00',
            'confidence_score': 1.0,
            'access_count': 0,
            'last_accessed': '2024-01-01T00:00:00+00:00',
            'rank': 0.5
        }
        mock_conn.fetch.return_value = [mock_row]
        
        results = await memory.recall("keywords", search_type=SearchType.TEXT)
        
        assert len(results) == 1
        assert results[0].content == "Test content with keywords"
        assert results[0].relevance_score == 0.5
        
        # Verify text search SQL was used
        mock_conn.fetch.assert_called_once()
        search_call = mock_conn.fetch.call_args[0]
        assert "to_tsvector" in search_call[0].lower() or "ilike" in search_call[0].lower()
    
    @pytest.mark.asyncio
    async def test_semantic_search_without_provider_raises_error(self, mock_asyncpg_pool):
        """Test semantic search without embedding provider raises error."""
        with patch('cogency.memory.pgvector.asyncpg') as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_asyncpg_pool[0])
            
            from cogency.memory.pgvector import PGVectorMemory
            memory = PGVectorMemory("postgresql://test")  # No embedding provider
            memory._pool = mock_asyncpg_pool[0]
            memory._initialized = True
            
            with pytest.raises(ValueError, match="Semantic search requested but no embedding provider available"):
                await memory.recall("test", search_type=SearchType.SEMANTIC)
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self, pgvector_memory):
        """Test hybrid search combines semantic and text results."""
        memory, mock_conn = pgvector_memory
        
        # Mock different responses for semantic and text searches
        semantic_row = {
            'id': uuid4(),
            'content': 'Semantic match',
            'memory_type': 'fact',
            'tags': [],
            'metadata': '{}',
            'created_at': '2024-01-01T00:00:00+00:00',
            'confidence_score': 1.0,
            'access_count': 0,
            'last_accessed': '2024-01-01T00:00:00+00:00',
            'similarity': 0.9
        }
        
        text_row = {
            'id': uuid4(),
            'content': 'Text match with query',
            'memory_type': 'fact',
            'tags': [],
            'metadata': '{}',
            'created_at': '2024-01-01T00:00:00+00:00',
            'confidence_score': 1.0,
            'access_count': 0,
            'last_accessed': '2024-01-01T00:00:00+00:00',
            'rank': 0.7
        }
        
        # Configure mock to return different results for different calls
        mock_conn.fetch.side_effect = [[semantic_row], [text_row]]
        
        results = await memory.recall("query", search_type=SearchType.HYBRID)
        
        assert len(results) == 2
        assert any("Semantic" in r.content for r in results)
        assert any("Text" in r.content for r in results)
        
        # Verify both searches were called
        assert mock_conn.fetch.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, pgvector_memory):
        """Test search with memory type, tags, and metadata filters."""
        memory, mock_conn = pgvector_memory
        
        mock_conn.fetch.return_value = []
        
        await memory.recall(
            "test query",
            search_type=SearchType.TEXT,
            memory_type=MemoryType.CONTEXT,
            tags=["important"],
            metadata_filter={"category": "work"}
        )
        
        # Verify filters were applied in SQL
        mock_conn.fetch.assert_called_once()
        search_call = mock_conn.fetch.call_args[0]
        sql = search_call[0]
        params = search_call[1:]
        
        assert "memory_type" in sql
        assert "tags" in sql
        assert "metadata" in sql
        assert MemoryType.CONTEXT.value in params
        assert ["important"] in params
    
    @pytest.mark.asyncio
    async def test_forget_artifact(self, pgvector_memory):
        """Test forgetting an artifact."""
        memory, mock_conn = pgvector_memory
        
        artifact_id = uuid4()
        mock_conn.execute.return_value = "DELETE 1"
        
        result = await memory.forget(artifact_id)
        
        assert result is True
        mock_conn.execute.assert_called_once()
        delete_call = mock_conn.execute.call_args[0]
        assert "DELETE FROM" in delete_call[0]
        assert artifact_id in delete_call[1:]
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, pgvector_memory):
        """Test clearing all memory."""
        memory, mock_conn = pgvector_memory
        
        await memory.clear()
        
        mock_conn.execute.assert_called_once()
        truncate_call = mock_conn.execute.call_args[0]
        assert "TRUNCATE TABLE" in truncate_call[0]
    
    @pytest.mark.asyncio
    async def test_close_cleanup(self, pgvector_memory):
        """Test proper cleanup on close."""
        memory, _ = pgvector_memory
        
        memory._pool.close = AsyncMock()
        
        await memory.close()
        
        memory._pool.close.assert_called_once()
        assert memory._pool is None
        assert memory._initialized is False
    
    @pytest.mark.asyncio
    async def test_inspect_returns_stats(self, pgvector_memory):
        """Test inspect returns PostgreSQL stats."""
        memory, mock_conn = pgvector_memory
        
        mock_conn.fetchval.side_effect = [5, "1024 kB"]  # count, size
        
        stats = await memory.inspect()
        
        assert "backend" in stats
        assert stats["backend"] == "pgvector"
        assert "table_name" in stats
        assert "vector_dimensions" in stats
        assert "count" in stats
        assert "table_size" in stats