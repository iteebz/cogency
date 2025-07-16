"""Shared fixtures and utilities for memory tests."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

from cogency.memory.base import SearchType, MemoryType, MemoryArtifact


@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider that returns predictable embeddings."""
    provider = Mock()
    provider.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return provider


@pytest.fixture
def sample_memory_artifact():
    """Sample memory artifact for testing."""
    return MemoryArtifact(
        id="test-artifact-id",
        content="Sample memory content",
        memory_type=MemoryType.FACT,
        tags=["test", "sample"],
        metadata={"source": "test"},
        created_at=datetime.now(timezone.utc),
        access_count=0,
        last_accessed=datetime.now(timezone.utc),
        user_id="test-user"
    )


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    return [0.1, 0.2, 0.3, 0.4, 0.5]


class MemoryCRUDTestUtils:
    """Reusable CRUD test patterns for memory backends."""
    
    @staticmethod
    async def test_memorize_basic(memory_backend, content="Test content"):
        """Test basic memorization functionality."""
        result = await memory_backend.memorize(
            content=content,
            memory_type=MemoryType.FACT,
            tags=["test"],
            metadata={"source": "test"}
        )
        return result
    
    @staticmethod
    async def test_recall_basic(memory_backend, query="test query"):
        """Test basic recall functionality."""
        results = await memory_backend.recall(
            query=query,
            search_type=SearchType.SEMANTIC,
            limit=5,
            threshold=0.7
        )
        return results
    
    @staticmethod
    async def test_forget_basic(memory_backend, artifact_id="test-id"):
        """Test basic forget functionality."""
        result = await memory_backend.forget(artifact_id=artifact_id)
        return result
    
    @staticmethod
    async def test_clear_basic(memory_backend):
        """Test basic clear functionality."""
        result = await memory_backend.clear()
        return result
    
    @staticmethod
    def assert_memory_artifact_structure(artifact):
        """Assert that an artifact has the correct structure."""
        assert hasattr(artifact, 'id')
        assert hasattr(artifact, 'content')
        assert hasattr(artifact, 'memory_type')
        assert hasattr(artifact, 'tags')
        assert hasattr(artifact, 'metadata')
        assert hasattr(artifact, 'created_at')
        assert hasattr(artifact, 'access_count')
        assert hasattr(artifact, 'last_accessed')
        assert hasattr(artifact, 'user_id')
    
    @staticmethod
    def create_mock_query_response(num_results=2, base_score=0.9):
        """Create mock query response with specified number of results."""
        matches = []
        for i in range(num_results):
            matches.append({
                'id': f'test-id-{i+1}',
                'score': base_score - (i * 0.1),
                'metadata': {
                    'content': f'Test content {i+1}',
                    'memory_type': 'fact' if i % 2 == 0 else 'episodic',
                    'tags': ['test'],
                    'created_at': '2024-01-01T00:00:00+00:00',
                    'access_count': i,
                    'last_accessed': '2024-01-01T00:00:00+00:00'
                }
            })
        return {'matches': matches}


@pytest.fixture
def memory_crud_utils():
    """Fixture providing CRUD test utilities."""
    return MemoryCRUDTestUtils()


# Pinecone-specific fixtures
@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for testing."""
    index = Mock()
    index.upsert = AsyncMock()
    index.query = AsyncMock()
    index.delete = AsyncMock()
    index.describe_index_stats = AsyncMock(return_value={'total_vector_count': 0})
    return index


# ChromaDB-specific fixtures
@pytest.fixture
def mock_chroma_collection():
    """Mock ChromaDB collection for testing."""
    collection = Mock()
    collection.add = AsyncMock()
    collection.query = AsyncMock()
    collection.delete = AsyncMock()
    collection.count = AsyncMock(return_value=0)
    return collection


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client for testing."""
    client = Mock()
    client.get_or_create_collection = Mock()
    return client


# PGVector-specific fixtures
@pytest.fixture
def mock_asyncpg_pool():
    """Mock asyncpg connection pool for testing."""
    pool = Mock()
    
    # Mock connection context manager
    conn = Mock()
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock()
    
    pool.acquire = Mock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    return pool, conn


# Common test data
@pytest.fixture
def test_memory_data():
    """Common test data for memory operations."""
    return {
        "content": "Test memory content",
        "memory_type": MemoryType.FACT,
        "tags": ["test", "sample"],
        "metadata": {"source": "test", "importance": "high"},
        "user_id": "test-user"
    }


@pytest.fixture
def test_query_params():
    """Common query parameters for testing."""
    return {
        "query": "test query",
        "search_type": SearchType.SEMANTIC,
        "limit": 5,
        "threshold": 0.7,
        "tags": ["test"],
        "memory_type": MemoryType.FACT
    }