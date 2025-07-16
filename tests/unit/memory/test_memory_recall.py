"""Tests for memory recall functionality across search types."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from cogency.memory.filesystem import FSMemory
from cogency.memory.base import MemoryArtifact, MemoryType, SearchType


@pytest.fixture
def fs_memory(tmp_path):
    """Fixture for FSMemory instance with a temporary directory."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FSMemory(memory_dir=str(memory_dir))


@pytest.fixture
def mock_embedding_provider():
    """Fixture for mock embedding provider."""
    provider = Mock()
    provider.embed = AsyncMock()
    provider.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    return provider


@pytest.fixture
def fs_memory_with_embeddings(tmp_path, mock_embedding_provider):
    """Fixture for FSMemory with embedding provider."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FSMemory(memory_dir=str(memory_dir), embedding_provider=mock_embedding_provider)


class TestRecallBasics:
    """Test basic recall functionality."""
    
    @pytest.mark.asyncio
    async def test_recall_empty_memory(self, fs_memory):
        """Test recall when no artifacts are stored."""
        results = await fs_memory.recall("query")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_recall_basic_match(self, fs_memory):
        """Test basic recall functionality with a matching artifact."""
        content = "This is a test about software engineering."
        await fs_memory.memorize(content, tags=["work"])

        results = await fs_memory.recall("software engineering", search_type=SearchType.TEXT)
        assert len(results) == 1
        assert results[0].content == content
        assert results[0].relevance_score > 0
    
    @pytest.mark.asyncio
    async def test_recall_with_limit(self, fs_memory):
        """Test recall with a specified limit."""
        await fs_memory.memorize("apple content")
        await fs_memory.memorize("banana content")
        await fs_memory.memorize("orange content")

        results = await fs_memory.recall("content", limit=2, search_type=SearchType.TEXT)
        assert len(results) == 2


class TestRecallFiltering:
    """Test recall filtering functionality."""
    
    @pytest.mark.asyncio
    async def test_recall_with_tags_filter(self, fs_memory):
        """Test recall filtering by tags."""
        await fs_memory.memorize("content with tag A", tags=["A"])
        await fs_memory.memorize("content with tag B", tags=["B"])
        await fs_memory.memorize("content with tag A and B", tags=["A", "B"])

        results = await fs_memory.recall("content", tags=["A"], search_type=SearchType.TEXT)
        assert len(results) == 2
        assert all("A" in art.tags for art in results)

        results = await fs_memory.recall("content", tags=["B"], search_type=SearchType.TEXT)
        assert len(results) == 2
        assert all("B" in art.tags for art in results)
    
    @pytest.mark.asyncio
    async def test_recall_with_memory_type_filter(self, fs_memory):
        """Test recall filtering by memory type."""
        await fs_memory.memorize("fact content", memory_type=MemoryType.FACT)
        await fs_memory.memorize("context content", memory_type=MemoryType.CONTEXT)

        results = await fs_memory.recall("content", memory_type=MemoryType.FACT, search_type=SearchType.TEXT)
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.FACT

        results = await fs_memory.recall("content", memory_type=MemoryType.CONTEXT, search_type=SearchType.TEXT)
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.CONTEXT
    
    @pytest.mark.asyncio
    async def test_metadata_filter_functionality(self, fs_memory):
        """Test metadata filtering in recall."""
        await fs_memory.memorize("content A", metadata={"category": "work", "priority": "high"})
        await fs_memory.memorize("content B", metadata={"category": "personal", "priority": "low"})
        await fs_memory.memorize("content C", metadata={"category": "work", "priority": "low"})
        
        # Filter by single metadata field
        results = await fs_memory.recall("content", metadata_filter={"category": "work"}, search_type=SearchType.TEXT)
        assert len(results) == 2
        assert all(art.metadata["category"] == "work" for art in results)
        
        # Filter by multiple metadata fields
        results = await fs_memory.recall("content", metadata_filter={"category": "work", "priority": "high"}, search_type=SearchType.TEXT)
        assert len(results) == 1
        assert results[0].content == "content A"


class TestRecallRelevanceScoring:
    """Test recall relevance scoring."""
    
    @pytest.mark.asyncio
    async def test_recall_relevance_scoring(self, fs_memory):
        """Test that relevance scoring prioritizes better matches."""
        await fs_memory.memorize("The quick brown fox jumps over the lazy dog.")
        await fs_memory.memorize("Foxes are known for their agility.")
        await fs_memory.memorize("A red fox was spotted in the forest.")

        results = await fs_memory.recall("fox", search_type=SearchType.TEXT)
        # Expecting artifacts with "fox" to be ranked higher
        assert len(results) == 3
        # The exact phrase "red fox" should score higher than just "fox"
        # This is a simplified check, actual scores depend on _calculate_relevance
        assert "red fox" in results[0].content.lower() or "foxes" in results[0].content.lower()


class TestRecallAccessStats:
    """Test recall access statistics tracking."""
    
    @pytest.mark.asyncio
    async def test_update_access_stats(self, fs_memory):
        """Test that access stats are updated on recall."""
        artifact = await fs_memory.memorize("Content for access stats.")
        original_access_count = artifact.access_count
        original_last_accessed = artifact.last_accessed

        # Recall the artifact to trigger access stat update
        results = await fs_memory.recall("Content for access stats.", search_type=SearchType.TEXT)
        assert len(results) == 1
        recalled_artifact = results[0]

        # Verify stats are updated in the returned artifact
        assert recalled_artifact.access_count == original_access_count + 1
        assert recalled_artifact.last_accessed > original_last_accessed

        # Give async file update time to complete
        import asyncio
        await asyncio.sleep(0.1)
        
        # Verify stats are updated in the file on disk
        file_path = fs_memory._get_user_memory_dir() / f"{recalled_artifact.id}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data["access_count"] == original_access_count + 1


class TestSemanticRecall:
    """Test semantic recall functionality."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_provider(self, fs_memory_with_embeddings, mock_embedding_provider):
        """Test semantic search using cosine similarity."""
        # Store content with embedding
        await fs_memory_with_embeddings.memorize("machine learning algorithms")
        
        # Mock query embedding - similar to stored embedding
        mock_embedding_provider.embed.return_value = [0.11, 0.21, 0.31, 0.41, 0.51]  # Slightly different
        
        results = await fs_memory_with_embeddings.recall("deep learning", search_type=SearchType.SEMANTIC, threshold=0.8)
        
        # Should find the similar content
        assert len(results) == 1
        assert results[0].content == "machine learning algorithms"
        assert results[0].relevance_score > 0.8
    
    @pytest.mark.asyncio
    async def test_semantic_search_threshold_filtering(self, fs_memory_with_embeddings, mock_embedding_provider):
        """Test semantic search respects similarity threshold."""
        await fs_memory_with_embeddings.memorize("completely different content")
        
        # Mock very different query embedding
        mock_embedding_provider.embed.return_value = [-0.5, -0.4, -0.3, -0.2, -0.1]
        
        results = await fs_memory_with_embeddings.recall("unrelated query", search_type=SearchType.SEMANTIC, threshold=0.9)
        
        # Should not find content due to low similarity
        assert len(results) == 0


class TestTextRecall:
    """Test text-based recall functionality."""
    
    @pytest.mark.asyncio
    async def test_text_search_functionality(self, fs_memory):
        """Test text search works as before."""
        await fs_memory.memorize("python programming tutorial")
        await fs_memory.memorize("javascript web development")
        
        results = await fs_memory.recall("python", search_type=SearchType.TEXT)
        assert len(results) == 1
        assert "python" in results[0].content.lower()


class TestHybridRecall:
    """Test hybrid recall functionality."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combines_methods(self, fs_memory_with_embeddings, mock_embedding_provider):
        """Test hybrid search combines semantic and text results."""
        await fs_memory_with_embeddings.memorize("python machine learning")  # Should match both
        await fs_memory_with_embeddings.memorize("deep learning neural networks")  # Semantic only
        await fs_memory_with_embeddings.memorize("python web development")  # Text only
        
        # Mock semantic similarity for ML content
        mock_embedding_provider.embed.return_value = [0.12, 0.22, 0.32, 0.42, 0.52]
        
        results = await fs_memory_with_embeddings.recall("python", search_type=SearchType.HYBRID, threshold=0.5)
        
        # Should find multiple results with combined scoring
        assert len(results) >= 2  # At least text matches, possibly semantic too