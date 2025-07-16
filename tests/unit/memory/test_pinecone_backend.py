"""Tests for Pinecone memory backend."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from cogency.memory.base import MemoryType, SearchType


class TestPineconeMemory:
    """Test Pinecone memory backend with mocked dependencies."""
    
    @pytest.fixture
    def mock_embedding_provider(self):
        """Mock embedding provider."""
        provider = Mock()
        provider.embed = AsyncMock()
        provider.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return provider
    
    @pytest.fixture
    def mock_pinecone_client(self):
        """Mock Pinecone client and index."""
        client = Mock()
        index = Mock()
        
        # Mock client methods
        client.list_indexes.return_value = [Mock(name="test-index")]
        client.create_index = Mock()
        client.delete_index = Mock()
        client.Index.return_value = index
        
        # Mock index methods
        index.upsert = Mock()
        index.query.return_value = Mock(matches=[])
        index.fetch.return_value = Mock(vectors={})
        index.delete = Mock()
        index.describe_index_stats.return_value = Mock(
            total_vector_count=100,
            dimension=1536,
            index_fullness=0.1
        )
        
        return client, index
    
    @pytest.fixture
    def pinecone_memory(self, mock_embedding_provider, mock_pinecone_client):
        """Pinecone memory instance with mocked dependencies."""
        with patch('cogency.memory.pinecone.Pinecone') as mock_pinecone_class:
            mock_pinecone_class.return_value = mock_pinecone_client[0]
            
            from cogency.memory.pinecone import PineconeMemory
            memory = PineconeMemory(
                api_key="test-key",
                index_name="test-index",
                embedding_provider=mock_embedding_provider
            )
            memory._client = mock_pinecone_client[0]
            memory._index = mock_pinecone_client[1]
            memory._initialized = True
            
            return memory, mock_pinecone_client[1]
    
    @pytest.mark.asyncio
    async def test_import_error_without_pinecone(self):
        """Test that ImportError is raised when pinecone is not available."""
        with patch('cogency.memory.pinecone.Pinecone', None):
            with pytest.raises(ImportError, match="pinecone-client is required"):
                from cogency.memory.pinecone import PineconeMemory
                PineconeMemory("test-key", "test-index")
    
    @pytest.mark.asyncio
    async def test_init_requires_embedding_provider(self):
        """Test that embedding provider is required for Pinecone."""
        with patch('cogency.memory.pinecone.Pinecone'):
            from cogency.memory.pinecone import PineconeMemory
            
            with pytest.raises(ValueError, match="embedding_provider is required"):
                PineconeMemory("test-key", "test-index")  # No embedding provider
    
    @pytest.mark.asyncio
    async def test_memorize_with_embedding(self, pinecone_memory, mock_embedding_provider):
        """Test memorizing content with embedding generation."""
        memory, mock_index = pinecone_memory
        
        content = "Test content for memorization"
        artifact = await memory.memorize(content, tags=["test"])
        
        assert artifact.content == content
        assert artifact.tags == ["test"]
        assert artifact.memory_type == MemoryType.FACT
        
        # Verify embedding was generated
        mock_embedding_provider.embed.assert_called_once_with(content)
        
        # Verify upsert was called with correct data
        mock_index.upsert.assert_called_once()
        upsert_call = mock_index.upsert.call_args[1]
        vectors = upsert_call["vectors"]
        assert len(vectors) == 1
        
        vector_id, embedding, metadata = vectors[0]
        assert vector_id == str(artifact.id)
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert metadata["content"] == content
        assert metadata["memory_type"] == "fact"
        assert metadata["tags"] == ["test"]
    
    @pytest.mark.asyncio
    async def test_memorize_embedding_failure_raises_error(self, pinecone_memory, mock_embedding_provider):
        """Test that memorize fails when embedding generation fails."""
        memory, _ = pinecone_memory
        
        # Mock embedding failure
        mock_embedding_provider.embed.return_value = None
        
        with pytest.raises(ValueError, match="Failed to generate embedding"):
            await memory.memorize("Test content")
    
    @pytest.mark.asyncio
    async def test_semantic_search_success(self, pinecone_memory, mock_embedding_provider):
        """Test semantic search with successful results."""
        memory, mock_index = pinecone_memory
        
        # Mock Pinecone response
        mock_match = Mock()
        mock_match.id = str(uuid4())
        mock_match.score = 0.85
        mock_match.metadata = {
            "content": "Test content",
            "memory_type": "fact",
            "tags": ["test"],
            "metadata": "{}",
            "created_at": "2024-01-01T00:00:00+00:00",
            "confidence_score": 1.0,
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00"
        }
        
        mock_index.query.return_value = Mock(matches=[mock_match])
        
        results = await memory.recall("test query", search_type=SearchType.SEMANTIC, threshold=0.8)
        
        assert len(results) == 1
        assert results[0].content == "Test content"
        assert results[0].relevance_score == 0.85
        
        # Verify embedding was generated for query
        mock_embedding_provider.embed.assert_called_with("test query")
        
        # Verify Pinecone query was called
        mock_index.query.assert_called_once()
        query_call = mock_index.query.call_args[1]
        assert query_call["vector"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert query_call["top_k"] == 10
        assert query_call["include_metadata"] is True
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, pinecone_memory):
        """Test semantic search with filters."""
        memory, mock_index = pinecone_memory
        
        mock_index.query.return_value = Mock(matches=[])
        
        await memory.recall(
            "test query",
            search_type=SearchType.SEMANTIC,
            memory_type=MemoryType.CONTEXT,
            tags=["important"]
        )
        
        # Verify filters were applied
        mock_index.query.assert_called_once()
        query_call = mock_index.query.call_args[1]
        assert "filter" in query_call
        
        filter_dict = query_call["filter"]
        assert filter_dict["memory_type"]["$eq"] == "context"
        assert filter_dict["tags"]["$in"] == ["important"]
    
    @pytest.mark.asyncio
    async def test_text_search_fallback_to_semantic(self, pinecone_memory):
        """Test that text search falls back to semantic search in Pinecone."""
        memory, mock_index = pinecone_memory
        
        mock_index.query.return_value = Mock(matches=[])
        
        # Request text search, should fallback to semantic
        await memory.recall("test query", search_type=SearchType.TEXT)
        
        # Verify semantic search was used
        mock_index.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hybrid_search_same_as_semantic(self, pinecone_memory):
        """Test that hybrid search behaves like semantic with lower threshold."""
        memory, mock_index = pinecone_memory
        
        mock_index.query.return_value = Mock(matches=[])
        
        await memory.recall("test query", search_type=SearchType.HYBRID, threshold=0.8)
        
        # Verify search was called (should use threshold * 0.7 = 0.56)
        mock_index.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_access_stats(self, pinecone_memory):
        """Test updating access statistics in Pinecone."""
        memory, mock_index = pinecone_memory
        
        artifact_id = uuid4()
        
        # Mock fetch response
        mock_vector = Mock()
        mock_vector.metadata = {
            "content": "Test content",
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00"
        }
        mock_vector.values = [0.1, 0.2, 0.3]
        
        mock_index.fetch.return_value = Mock(vectors={str(artifact_id): mock_vector})
        
        # Create mock artifact
        from cogency.memory.base import MemoryArtifact
        artifact = MemoryArtifact(id=artifact_id, content="Test content")
        artifact.access_count = 5
        
        await memory._update_access_stats_pinecone(artifact)
        
        # Verify fetch and upsert were called
        mock_index.fetch.assert_called_once_with(ids=[str(artifact_id)])
        mock_index.upsert.assert_called_once()
        
        # Verify updated metadata
        upsert_call = mock_index.upsert.call_args[1]
        updated_metadata = upsert_call["vectors"][0][2]
        assert updated_metadata["access_count"] == 5
    
    @pytest.mark.asyncio
    async def test_forget_artifact(self, pinecone_memory):
        """Test forgetting an artifact."""
        memory, mock_index = pinecone_memory
        
        artifact_id = uuid4()
        
        result = await memory.forget(artifact_id)
        
        assert result is True
        mock_index.delete.assert_called_once_with(ids=[str(artifact_id)])
    
    @pytest.mark.asyncio
    async def test_forget_artifact_failure(self, pinecone_memory):
        """Test forgetting an artifact when delete fails."""
        memory, mock_index = pinecone_memory
        
        mock_index.delete.side_effect = Exception("Delete failed")
        
        result = await memory.forget(uuid4())
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear_memory_recreates_index(self, pinecone_memory):
        """Test clearing memory by recreating index."""
        memory, _ = pinecone_memory
        client = memory._client
        
        await memory.clear()
        
        # Verify index was deleted and recreated
        client.delete_index.assert_called_once_with("test-index")
        client.create_index.assert_called_once()
        client.Index.assert_called()  # Reconnected to new index
    
    @pytest.mark.asyncio
    async def test_close_cleanup(self, pinecone_memory):
        """Test proper cleanup on close."""
        memory, _ = pinecone_memory
        
        await memory.close()
        
        assert memory._client is None
        assert memory._index is None
        assert memory._initialized is False
    
    @pytest.mark.asyncio
    async def test_inspect_returns_stats(self, pinecone_memory):
        """Test inspect returns Pinecone stats."""
        memory, mock_index = pinecone_memory
        
        stats = await memory.inspect()
        
        assert "backend" in stats
        assert stats["backend"] == "pinecone"
        assert "index_name" in stats
        assert stats["index_name"] == "test-index"
        assert "total_vector_count" in stats
        assert stats["total_vector_count"] == 100
        assert "dimension" in stats
        assert stats["dimension"] == 1536
        
        # Verify stats were fetched from index
        mock_index.describe_index_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_determine_search_type_logic(self, pinecone_memory):
        """Test search type determination logic."""
        memory, _ = pinecone_memory
        
        # AUTO should become SEMANTIC
        assert memory._determine_search_type(SearchType.AUTO) == SearchType.SEMANTIC
        
        # TEXT should become SEMANTIC (fallback)
        assert memory._determine_search_type(SearchType.TEXT) == SearchType.SEMANTIC
        
        # SEMANTIC stays SEMANTIC
        assert memory._determine_search_type(SearchType.SEMANTIC) == SearchType.SEMANTIC
        
        # HYBRID stays HYBRID
        assert memory._determine_search_type(SearchType.HYBRID) == SearchType.HYBRID