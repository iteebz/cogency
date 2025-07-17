"""Unit tests for ChromaDBMemory implementation."""

import pytest
from unittest.mock import patch

from cogency.memory.backends.chroma import ChromaBackend
from cogency.memory.core import SearchType, MemoryType
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from memory.memory_crud import crud_memorize, crud_recall, crud_forget, crud_clear, mock_vector_response, assert_artifact


@pytest.fixture
def chromadb_memory(mock_embedding_provider, mock_chroma_client, mock_chroma_collection):
    mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection
    mock_chroma_client.get_collection.side_effect = Exception("Collection not found")
    mock_chroma_client.create_collection.return_value = mock_chroma_collection
    
    with patch('chromadb.Client', return_value=mock_chroma_client):
        memory = ChromaBackend(
            collection_name="test-collection",
            embedding_provider=mock_embedding_provider
        )
        # Pre-set the collection and client to avoid async initialization issues
        memory._client = mock_chroma_client
        memory._collection = mock_chroma_collection
        memory._initialized = True
    return memory


@pytest.mark.asyncio
class TestChromaDBMemory:
    
    async def test_memorize(self, chromadb_memory, mock_chroma_collection):
        await crud_memorize(chromadb_memory, "test content")
        
        mock_chroma_collection.add.assert_called_once()
        call_args = mock_chroma_collection.add.call_args[1]
        assert call_args["embeddings"][0] == [0.1, 0.2, 0.3]
        assert call_args["documents"][0] == "test content"
    
    async def test_memorize_no_embedding_fails(self, mock_chroma_client, mock_chroma_collection):
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection
        
        with patch('chromadb.Client', return_value=mock_chroma_client):
            memory = ChromaBackend(collection_name="test-collection")
        
        with pytest.raises(ValueError, match="Embedding provider required"):
            await crud_memorize(memory)
    
    async def test_recall(self, chromadb_memory, mock_chroma_collection):
        mock_response = {
            'ids': [['id-1', 'id-2']],
            'distances': [[0.1, 0.2]],
            'documents': [['Content 1', 'Content 2']],
            'metadatas': [[
                {'memory_type': 'fact', 'tags': ['test'], 'created_at': '2024-01-01T00:00:00+00:00', 'access_count': 0, 'last_accessed': '2024-01-01T00:00:00+00:00'},
                {'memory_type': 'fact', 'tags': ['test'], 'created_at': '2024-01-01T00:00:00+00:00', 'access_count': 0, 'last_accessed': '2024-01-01T00:00:00+00:00'}
            ]]
        }
        mock_chroma_collection.query.return_value = mock_response
        
        results = await crud_recall(chromadb_memory)
        
        assert len(results) == 2
        assert_artifact(results[0], "Content 1", MemoryType.FACT)
        
        call_args = mock_chroma_collection.query.call_args[1]
        assert call_args["query_embeddings"][0] == [0.1, 0.2, 0.3]
        assert call_args["n_results"] == 5
    
    async def test_recall_with_filters(self, chromadb_memory, mock_chroma_collection):
        mock_chroma_collection.query.return_value = {'ids': [[]], 'distances': [[]], 'documents': [[]], 'metadatas': [[]]}
        
        await chromadb_memory.recall(
            query="test",
            tags=["important"],
            memory_type=MemoryType.FACT,
            metadata_filter={"source": "api"}
        )
        
        expected_where = {
            "$and": [
                {"tags": {"$in": ["important"]}},
                {"memory_type": "fact"},
                {"source": "api"}
            ]
        }
        assert mock_chroma_collection.query.call_args[1]["where"] == expected_where
    
    async def test_recall_threshold_filtering(self, chromadb_memory, mock_chroma_collection):
        mock_response = {
            'ids': [['high-score', 'low-score']],
            'distances': [[0.1, 0.5]],  # ChromaDB uses distance (lower = better)
            'documents': [['High relevance', 'Low relevance']],
            'metadatas': [[
                {'memory_type': 'fact', 'created_at': '2024-01-01T00:00:00+00:00', 'access_count': 0, 'last_accessed': '2024-01-01T00:00:00+00:00'},
                {'memory_type': 'fact', 'created_at': '2024-01-01T00:00:00+00:00', 'access_count': 0, 'last_accessed': '2024-01-01T00:00:00+00:00'}
            ]]
        }
        mock_chroma_collection.query.return_value = mock_response
        
        results = await crud_recall(chromadb_memory, threshold=0.7)  # 0.7 similarity = 0.3 distance
        
        assert len(results) == 1
        assert_artifact(results[0], "High relevance")
    
    async def test_text_search_not_supported(self, chromadb_memory):
        with pytest.raises(NotImplementedError, match="Text search not supported"):
            await chromadb_memory.recall("test", search_type=SearchType.TEXT)
    
    async def test_hybrid_search_not_supported(self, chromadb_memory):
        with pytest.raises(NotImplementedError, match="Hybrid search not supported"):
            await chromadb_memory.recall("test", search_type=SearchType.HYBRID)
    
    async def test_forget(self, chromadb_memory, mock_chroma_collection):
        assert await crud_forget(chromadb_memory) is True
        mock_chroma_collection.delete.assert_called_once_with(ids=["test-id"])
    
    async def test_forget_with_filters(self, chromadb_memory, mock_chroma_collection):
        result = await chromadb_memory.forget(
            tags=["old"],
            metadata_filter={"source": "deprecated"}
        )
        
        assert result is True
        expected_where = {
            "$and": [
                {"tags": {"$in": ["old"]}},
                {"source": "deprecated"}
            ]
        }
        mock_chroma_collection.delete.assert_called_once_with(where=expected_where)
    
    async def test_forget_no_criteria_fails(self, chromadb_memory):
        with pytest.raises(ValueError, match="Must provide either artifact_id or filters"):
            await chromadb_memory.forget()
    
    async def test_clear(self, chromadb_memory, mock_chroma_collection):
        assert await crud_clear(chromadb_memory) is True
        mock_chroma_collection.delete.assert_called_once()
    
    async def test_stats(self, chromadb_memory, mock_chroma_collection):
        mock_chroma_collection.count.return_value = 100
        
        stats = await chromadb_memory.get_stats()
        
        assert stats['total_memories'] == 100
        assert stats['backend'] == 'chromadb'