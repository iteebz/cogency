"""Unit tests for PineconeMemory implementation."""

import pytest
from unittest.mock import patch

from cogency.memory.backends.pinecone import PineconeBackend
from cogency.memory.core import SearchType, MemoryType
from .memory_crud import crud_memorize, crud_recall, crud_forget, crud_clear, mock_vector_response, assert_artifact


@pytest.fixture
def pinecone_memory(mock_embedding_provider, mock_pinecone_index):
    with patch('pinecone.Index', return_value=mock_pinecone_index):
        memory = PineconeBackend(
            api_key="test-key",
            index_name="test-index",
            embedding_provider=mock_embedding_provider
        )
        memory.index = mock_pinecone_index
    return memory


@pytest.mark.asyncio
class TestPineconeMemory:
    
    async def test_memorize(self, pinecone_memory, mock_pinecone_index):
        await crud_memorize(pinecone_memory, "test content")
        
        mock_pinecone_index.upsert.assert_called_once()
        vector = mock_pinecone_index.upsert.call_args[1]["vectors"][0]
        assert vector["values"] == [0.1, 0.2, 0.3]
        assert vector["metadata"]["content"] == "test content"
    
    async def test_memorize_no_embedding_fails(self, mock_pinecone_index):
        with patch('pinecone.Index', return_value=mock_pinecone_index):
            memory = PineconeBackend(api_key="test-key", index_name="test-index")
        
        with pytest.raises(ValueError, match="Embedding provider required"):
            await crud_memorize(memory)
    
    async def test_recall(self, pinecone_memory, mock_pinecone_index):
        mock_pinecone_index.query.return_value = mock_vector_response([0.9, 0.8])
        
        results = await crud_recall(pinecone_memory)
        
        assert len(results) == 2
        assert_artifact(results[0], "Content 1", MemoryType.FACT)
        
        call_args = mock_pinecone_index.query.call_args[1]
        assert call_args["vector"] == [0.1, 0.2, 0.3]
        assert call_args["top_k"] == 5
    
    async def test_recall_with_filters(self, pinecone_memory, mock_pinecone_index):
        mock_pinecone_index.query.return_value = {'matches': []}
        
        await pinecone_memory.recall(
            query="test",
            tags=["important"],
            memory_type=MemoryType.FACT,
            metadata_filter={"source": "api"}
        )
        
        expected_filter = {
            "$and": [
                {"tags": {"$in": ["important"]}},
                {"memory_type": "fact"},
                {"source": "api"}
            ]
        }
        assert mock_pinecone_index.query.call_args[1]["filter"] == expected_filter
    
    async def test_recall_threshold_filtering(self, pinecone_memory, mock_pinecone_index):
        mock_pinecone_index.query.return_value = mock_vector_response([0.9, 0.5])
        
        results = await crud_recall(pinecone_memory, threshold=0.7)
        
        assert len(results) == 1
        assert_artifact(results[0], "Content 1")
    
    async def test_text_search_not_supported(self, pinecone_memory):
        with pytest.raises(NotImplementedError, match="Text search not supported"):
            await pinecone_memory.recall("test", search_type=SearchType.TEXT)
    
    async def test_hybrid_search_not_supported(self, pinecone_memory):
        with pytest.raises(NotImplementedError, match="Hybrid search not supported"):
            await pinecone_memory.recall("test", search_type=SearchType.HYBRID)
    
    async def test_forget(self, pinecone_memory, mock_pinecone_index):
        assert await crud_forget(pinecone_memory) is True
        mock_pinecone_index.delete.assert_called_once_with(ids=["test-id"])
    
    async def test_forget_with_filters(self, pinecone_memory, mock_pinecone_index):
        result = await pinecone_memory.forget(
            tags=["old"],
            metadata_filter={"source": "deprecated"}
        )
        
        assert result is True
        expected_filter = {
            "$and": [
                {"tags": {"$in": ["old"]}},
                {"source": "deprecated"}
            ]
        }
        mock_pinecone_index.delete.assert_called_once_with(filter=expected_filter)
    
    async def test_forget_no_criteria_fails(self, pinecone_memory):
        with pytest.raises(ValueError, match="Must provide either artifact_id or filters"):
            await pinecone_memory.forget()
    
    async def test_clear(self, pinecone_memory, mock_pinecone_index):
        assert await crud_clear(pinecone_memory) is True
        mock_pinecone_index.delete.assert_called_once_with(delete_all=True)
    
    async def test_stats(self, pinecone_memory, mock_pinecone_index):
        mock_pinecone_index.describe_index_stats.return_value = {
            'total_vector_count': 100,
            'dimension': 384
        }
        
        stats = await pinecone_memory.get_stats()
        
        assert stats['total_memories'] == 100
        assert stats['backend'] == 'pinecone'