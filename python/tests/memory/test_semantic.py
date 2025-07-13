"""Tests for semantic memory implementation."""
import pytest
import asyncio
import tempfile
import shutil
import numpy as np
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from cogency.memory.semantic import SemanticMemory
from cogency.memory.base import MemoryArtifact
from cogency.embed.base import BaseEmbed


class MockEmbedProvider(BaseEmbed):
    """Mock embedding provider for testing."""
    
    def __init__(self):
        super().__init__()
        self._model = "mock-embed-v1"
        self._dimensionality = 4
        # Simple mock embeddings based on text length and content
        self._embeddings = {
            "python programming": np.array([1.0, 0.8, 0.2, 0.1]),
            "javascript coding": np.array([0.8, 1.0, 0.3, 0.2]),
            "database design": np.array([0.2, 0.3, 1.0, 0.8]),
            "machine learning": np.array([0.3, 0.2, 0.8, 1.0]),
            "python": np.array([1.0, 0.7, 0.1, 0.0]),  # Similar to "python programming"
            "programming": np.array([0.9, 0.8, 0.2, 0.1]),  # Similar to programming content
        }
    
    def embed_single(self, text: str, **kwargs) -> np.ndarray:
        # Return predefined embedding or generate based on hash for consistency
        if text.lower() in self._embeddings:
            return self._embeddings[text.lower()]
        
        # Generate consistent embedding based on text
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        np.random.seed(hash_val % 1000)
        return np.random.random(self._dimensionality)
    
    def embed_batch(self, texts: list[str], **kwargs) -> list[np.ndarray]:
        return [self.embed_single(text) for text in texts]
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def dimensionality(self) -> int:
        return self._dimensionality


@pytest.fixture
def temp_memory_dir():
    """Create temporary directory for memory tests."""
    temp_dir = tempfile.mkdtemp(prefix="cogency_semantic_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_embed_provider():
    """Create mock embedding provider."""
    return MockEmbedProvider()


@pytest.fixture
def semantic_memory(temp_memory_dir, mock_embed_provider):
    """Create SemanticMemory instance with mock provider."""
    return SemanticMemory(
        embed_provider=mock_embed_provider,
        memory_dir=temp_memory_dir,
        similarity_threshold=0.5
    )


@pytest.mark.asyncio
async def test_semantic_memory_initialization(semantic_memory):
    """Test SemanticMemory initialization."""
    assert semantic_memory.embed_provider is not None
    assert semantic_memory.memory_dir.exists()
    assert semantic_memory.similarity_threshold == 0.5


@pytest.mark.asyncio
async def test_memorize_with_embedding(semantic_memory, temp_memory_dir):
    """Test memorizing content with embedding generation."""
    content = "Python programming best practices"
    
    artifact = await semantic_memory.memorize(content, tags=["python", "programming"])
    
    # Check artifact
    assert artifact.content == content
    assert "python" in artifact.tags
    
    # Check file was created with embedding
    file_path = Path(temp_memory_dir) / f"{artifact.id}.json"
    assert file_path.exists()
    
    import json
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert data["embedding"] is not None
    assert len(data["embedding"]) == 4  # Mock embedding dimensionality
    assert data["embedding_model"] == "mock-embed-v1"


@pytest.mark.asyncio
async def test_semantic_recall_similarity(semantic_memory):
    """Test semantic recall using embedding similarity."""
    # Store content with known embeddings
    await semantic_memory.memorize("Python programming tips", tags=["python"])
    await semantic_memory.memorize("JavaScript coding patterns", tags=["javascript"])
    await semantic_memory.memorize("Database design principles", tags=["database"])
    
    # Query for python-related content
    results = await semantic_memory.recall("python", use_semantic=True)
    
    # Should find at least one result via semantic similarity
    assert len(results) >= 1
    
    # Test that semantic search is working by comparing to exact text search
    text_results = await semantic_memory.recall("python", use_semantic=False)
    
    # Semantic search might find different/more results than text search
    # The key is that it's using embeddings and similarity scoring
    assert isinstance(results, list)
    for result in results:
        assert hasattr(result, 'content')
        assert hasattr(result, 'tags')


@pytest.mark.asyncio
async def test_semantic_recall_vs_text_recall(semantic_memory):
    """Test difference between semantic and text-based recall."""
    # Store content
    await semantic_memory.memorize("Python programming fundamentals", tags=["python"])
    await semantic_memory.memorize("Machine learning algorithms", tags=["ml"])
    
    # Semantic search for "programming" should find python content
    semantic_results = await semantic_memory.recall("programming", use_semantic=True)
    
    # Text search for "programming" should find exact match
    text_results = await semantic_memory.recall("programming", use_semantic=False)
    
    # Both should find the python content, but semantic might find more
    assert len(semantic_results) >= 1
    assert len(text_results) >= 1


@pytest.mark.asyncio
async def test_similarity_threshold_filtering(semantic_memory):
    """Test that similarity threshold filters low-relevance results."""
    # Store diverse content
    await semantic_memory.memorize("Python programming", tags=["python"])
    await semantic_memory.memorize("Cooking recipes", tags=["cooking"])
    
    # Query with high threshold (should filter out cooking)
    semantic_memory.similarity_threshold = 0.9
    results = await semantic_memory.recall("python programming", use_semantic=True)
    
    # Should find only highly similar content
    assert all("Python" in result.content or "python" in [tag.lower() for tag in result.tags] 
              for result in results)


@pytest.mark.asyncio
async def test_fallback_to_text_search(semantic_memory):
    """Test fallback to text search when embedding fails."""
    # Mock embedding provider to fail
    def failing_embed(text):
        raise Exception("Embedding failed")
    
    semantic_memory.embed_provider.embed_single = failing_embed
    
    # Store content (should fall back gracefully)
    await semantic_memory.memorize("Test content", tags=["test"])
    
    # Recall should fall back to text search
    results = await semantic_memory.recall("Test", use_semantic=True)
    
    # Should still find content via text search fallback
    assert len(results) >= 1
    assert results[0].content == "Test content"


@pytest.mark.asyncio
async def test_tag_filtering_with_semantic_search(semantic_memory):
    """Test tag filtering in semantic search."""
    # Store content with different tags
    await semantic_memory.memorize("Python programming tips", tags=["python", "programming"])
    await semantic_memory.memorize("Python data science", tags=["python", "data"])
    await semantic_memory.memorize("JavaScript programming", tags=["javascript", "programming"])
    
    # Search for programming content filtered by python tag
    results = await semantic_memory.recall("programming", tags=["python"], use_semantic=True)
    
    assert len(results) >= 1
    for result in results:
        assert "python" in result.tags


@pytest.mark.asyncio
async def test_get_embedding_stats(semantic_memory):
    """Test embedding statistics reporting."""
    # Store some content
    await semantic_memory.memorize("Content with embedding", tags=["test"])
    await semantic_memory.memorize("Another content", tags=["test"])
    
    stats = semantic_memory.get_embedding_stats()
    
    assert stats["total_artifacts"] == 2
    assert stats["with_embeddings"] == 2
    assert stats["embedding_coverage"] == 1.0
    assert "mock-embed-v1" in stats["embedding_models"]
    assert stats["current_model"] == "mock-embed-v1"


@pytest.mark.asyncio
async def test_cosine_similarity_calculation(semantic_memory):
    """Test cosine similarity calculation."""
    # Test identical vectors
    a = np.array([1, 0, 0])
    b = np.array([1, 0, 0])
    similarity = semantic_memory._cosine_similarity(a, b)
    assert abs(similarity - 1.0) < 1e-6
    
    # Test orthogonal vectors
    a = np.array([1, 0, 0])
    b = np.array([0, 1, 0])
    similarity = semantic_memory._cosine_similarity(a, b)
    assert abs(similarity - 0.0) < 1e-6
    
    # Test zero vectors
    a = np.array([0, 0, 0])
    b = np.array([1, 0, 0])
    similarity = semantic_memory._cosine_similarity(a, b)
    assert similarity == 0.0


@pytest.mark.asyncio
async def test_recall_ordering_by_similarity(semantic_memory):
    """Test that semantic recall orders results by similarity score."""
    # Store content with varying similarity to query
    await semantic_memory.memorize("Python programming", tags=["python"])  # High similarity
    await semantic_memory.memorize("Database design", tags=["database"])   # Low similarity
    await semantic_memory.memorize("Programming languages", tags=["programming"])  # Medium similarity
    
    # Query should return results ordered by similarity
    results = await semantic_memory.recall("python programming", use_semantic=True, limit=3)
    
    assert len(results) >= 1
    # First result should be the most similar (exact match)
    assert "Python programming" in results[0].content


@pytest.mark.asyncio
async def test_recall_limit_with_semantic_search(semantic_memory):
    """Test result limiting in semantic search."""
    # Store multiple items
    for i in range(5):
        await semantic_memory.memorize(f"Python content {i}", tags=["python"])
    
    # Request limited results
    results = await semantic_memory.recall("python", limit=3, use_semantic=True)
    
    assert len(results) == 3