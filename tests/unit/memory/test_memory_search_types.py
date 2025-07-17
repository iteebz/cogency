"""Tests for memory search type functionality."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import SearchType


@pytest.fixture
def fs_memory(tmp_path):
    """Fixture for FilesystemBackend instance with a temporary directory."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FilesystemBackend(memory_dir=str(memory_dir))


@pytest.fixture
def mock_embedding_provider():
    """Fixture for mock embedding provider."""
    provider = Mock()
    provider.embed = AsyncMock()
    provider.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    return provider


@pytest.fixture
def fs_memory_with_embeddings(tmp_path, mock_embedding_provider):
    """Fixture for FilesystemBackend with embedding provider."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir(exist_ok=True)
    return FilesystemBackend(memory_dir=str(memory_dir), embedding_provider=mock_embedding_provider)


class TestSearchTypeLogic:
    """Test search type determination and handling."""
    
    @pytest.mark.asyncio
    async def test_search_type_auto_without_embeddings(self, fs_memory):
        """Test AUTO search type defaults to TEXT when no embedding provider."""
        await fs_memory.memorize("test content")
        
        results = await fs_memory.recall("test", search_type=SearchType.AUTO)
        assert len(results) == 1
        assert results[0].content == "test content"
    
    @pytest.mark.asyncio
    async def test_search_type_auto_with_embeddings(self, fs_memory_with_embeddings):
        """Test AUTO search type defaults to SEMANTIC when embedding provider available."""
        await fs_memory_with_embeddings.memorize("test content")
        
        results = await fs_memory_with_embeddings.recall("test", search_type=SearchType.AUTO)
        assert len(results) == 1
        assert results[0].content == "test content"
    
    @pytest.mark.asyncio
    async def test_determine_search_type_logic(self, fs_memory, fs_memory_with_embeddings):
        """Test search type determination logic."""
        # Without embedding provider, AUTO -> TEXT
        assert fs_memory._determine_search_type(SearchType.AUTO) == SearchType.TEXT
        assert fs_memory._determine_search_type(SearchType.TEXT) == SearchType.TEXT
        assert fs_memory._determine_search_type(SearchType.SEMANTIC) == SearchType.SEMANTIC
        
        # With embedding provider, AUTO -> SEMANTIC
        assert fs_memory_with_embeddings._determine_search_type(SearchType.AUTO) == SearchType.SEMANTIC
        assert fs_memory_with_embeddings._determine_search_type(SearchType.TEXT) == SearchType.TEXT


class TestSearchTypeErrors:
    """Test search type error handling."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_without_provider_raises_error(self, fs_memory):
        """Test semantic search without provider raises clear error."""
        await fs_memory.memorize("test content")
        
        with pytest.raises(ValueError, match="Semantic search requested but no embedding provider available"):
            await fs_memory.recall("test", search_type=SearchType.SEMANTIC)


class TestCosineSimilarity:
    """Test cosine similarity calculations."""
    
    @pytest.mark.asyncio
    async def test_cosine_similarity_calculation(self, fs_memory):
        """Test cosine similarity calculation."""
        # Test identical vectors
        similarity = fs_memory._cosine_similarity([1, 0, 0], [1, 0, 0])
        assert abs(similarity - 1.0) < 1e-10
        
        # Test orthogonal vectors
        similarity = fs_memory._cosine_similarity([1, 0], [0, 1])
        assert abs(similarity - 0.0) < 1e-10
        
        # Test opposite vectors
        similarity = fs_memory._cosine_similarity([1, 0], [-1, 0])
        assert abs(similarity - (-1.0)) < 1e-10
        
        # Test zero vector handling
        similarity = fs_memory._cosine_similarity([0, 0], [1, 1])
        assert similarity == 0.0