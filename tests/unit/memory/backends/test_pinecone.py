"""Unit tests for Pinecone backend implementation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from cogency.memory.core import SearchType, MemoryType
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from memory.memory_crud import crud_memorize, crud_recall, crud_forget, crud_clear, assert_artifact

# Skip all Pinecone tests if package not properly configured
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except Exception:
    PINECONE_AVAILABLE = False


@pytest.fixture
def mock_pinecone_client():
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
def pinecone_memory(mock_embedding_provider, mock_pinecone_client):
    """Pinecone memory instance with mocked dependencies."""
    client, index = mock_pinecone_client
    
    with patch('cogency.memory.backends.pinecone.Pinecone', return_value=client):
        from cogency.memory.backends.pinecone import PineconeBackend
        memory = PineconeBackend(
            api_key="test-key",
            index_name="test-index",
            embedding_provider=mock_embedding_provider
        )
        # Pre-set the client and index to avoid async initialization issues
        memory._client = client
        memory._index = index
        memory._initialized = True
        
    return memory


@pytest.mark.skipif(not PINECONE_AVAILABLE, reason="Pinecone package not properly configured")
@pytest.mark.asyncio
class TestPineconeBackend:
    
    async def test_memorize(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        await crud_memorize(pinecone_memory, "test content")
        
        index.upsert.assert_called_once()
        call_args = index.upsert.call_args[1]
        vectors = call_args["vectors"]
        assert len(vectors) == 1
        assert vectors[0][1] == [0.1, 0.2, 0.3]  # embedding
        assert vectors[0][2]["content"] == "test content"  # metadata
    
    async def test_memorize_no_embedding_fails(self, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        with patch('cogency.memory.backends.pinecone.Pinecone', return_value=client):
            memory = PineconeBackend(api_key="test-key", index_name="test-index")
        
        with pytest.raises(ValueError, match="Embedding provider required"):
            await crud_memorize(memory)
    
    async def test_recall(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        mock_match1 = Mock()
        mock_match1.id = "id-1"
        mock_match1.score = 0.9
        mock_match1.metadata = {
            "content": "Content 1",
            "memory_type": "fact",
            "tags": ["test"],
            "metadata": "{}",
            "created_at": "2024-01-01T00:00:00+00:00",
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00",
            "confidence_score": 1.0
        }
        
        mock_match2 = Mock()
        mock_match2.id = "id-2"
        mock_match2.score = 0.8
        mock_match2.metadata = {
            "content": "Content 2",
            "memory_type": "fact",
            "tags": ["test"],
            "metadata": "{}",
            "created_at": "2024-01-01T00:00:00+00:00",
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00",
            "confidence_score": 1.0
        }
        
        index.query.return_value = Mock(matches=[mock_match1, mock_match2])
        
        results = await crud_recall(pinecone_memory)
        
        assert len(results) == 2
        assert_artifact(results[0], "Content 1", MemoryType.FACT)
        assert results[0].relevance_score == 0.9
        
        index.query.assert_called_once()
        call_args = index.query.call_args[1]
        assert call_args["vector"] == [0.1, 0.2, 0.3]
        assert call_args["top_k"] == 5
        assert call_args["include_metadata"] is True
    
    async def test_recall_with_filters(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        index.query.return_value = Mock(matches=[])
        
        await pinecone_memory.recall(
            query="test",
            tags=["important"],
            memory_type=MemoryType.FACT,
            metadata_filter={"source": "api"}
        )
        
        expected_filter = {
            "tags": {"$in": ["important"]},
            "memory_type": {"$eq": "fact"},
            "source": {"$eq": "api"}
        }
        
        call_args = index.query.call_args[1]
        assert call_args["filter"] == expected_filter
    
    async def test_recall_threshold_filtering(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        high_score_match = Mock()
        high_score_match.id = "high-score"
        high_score_match.score = 0.9
        high_score_match.metadata = {
            "content": "High relevance",
            "memory_type": "fact",
            "tags": [],
            "metadata": "{}",
            "created_at": "2024-01-01T00:00:00+00:00",
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00",
            "confidence_score": 1.0
        }
        
        low_score_match = Mock()
        low_score_match.id = "low-score"
        low_score_match.score = 0.5
        low_score_match.metadata = {
            "content": "Low relevance",
            "memory_type": "fact",
            "tags": [],
            "metadata": "{}",
            "created_at": "2024-01-01T00:00:00+00:00",
            "access_count": 0,
            "last_accessed": "2024-01-01T00:00:00+00:00",
            "confidence_score": 1.0
        }
        
        index.query.return_value = Mock(matches=[high_score_match, low_score_match])
        
        results = await crud_recall(pinecone_memory, threshold=0.7)
        
        assert len(results) == 1
        assert_artifact(results[0], "High relevance")
    
    async def test_forget(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        assert await crud_forget(pinecone_memory) is True
        index.delete.assert_called_once_with(ids=["test-id"])
    
    async def test_forget_with_filters(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        result = await pinecone_memory.forget(
            tags=["old"],
            metadata_filter={"source": "deprecated"}
        )
        
        assert result is True
        expected_filter = {
            "tags": {"$in": ["old"]},
            "source": {"$eq": "deprecated"}
        }
        index.delete.assert_called_once_with(filter=expected_filter)
    
    async def test_forget_no_criteria_fails(self, pinecone_memory):
        with pytest.raises(ValueError, match="Must provide either artifact_id or filters"):
            await pinecone_memory.forget()
    
    async def test_clear(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        assert await crud_clear(pinecone_memory) is True
        index.delete.assert_called_once_with(delete_all=True)
    
    async def test_stats(self, pinecone_memory, mock_pinecone_client):
        client, index = mock_pinecone_client
        
        stats = await pinecone_memory.get_stats()
        
        assert stats['total_memories'] == 100
        assert stats['backend'] == 'pinecone'
        assert stats['index_name'] == 'test-index'
        assert stats['dimension'] == 1536
        assert stats['index_fullness'] == 0.1