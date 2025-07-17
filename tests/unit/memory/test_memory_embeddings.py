"""Tests for memory embedding functionality."""
import pytest
import json
from unittest.mock import Mock, AsyncMock

from cogency.memory.backends.filesystem import FilesystemBackend


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
    memory_dir.mkdir()
    return FilesystemBackend(memory_dir=str(memory_dir), embedding_provider=mock_embedding_provider)


class TestEmbeddingIntegration:
    """Test embedding provider integration."""
    
    @pytest.mark.asyncio
    async def test_memorize_with_embedding_provider(self, fs_memory_with_embeddings, mock_embedding_provider):
        """Test memorize stores embeddings when provider available."""
        content = "Test content for embedding"
        artifact = await fs_memory_with_embeddings.memorize(content)
        
        # Verify embedding provider was called
        mock_embedding_provider.embed.assert_called_once_with(content)
        
        # Verify embedding is stored in file
        file_path = fs_memory_with_embeddings._get_user_memory_dir() / f"{artifact.id}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["embedding"] == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    @pytest.mark.asyncio
    async def test_memorize_embedding_failure_graceful(self, fs_memory_with_embeddings, mock_embedding_provider):
        """Test memorize handles embedding failure gracefully."""
        mock_embedding_provider.embed.side_effect = Exception("Embedding failed")
        
        content = "Test content"
        artifact = await fs_memory_with_embeddings.memorize(content)
        
        # Should still create artifact
        assert artifact.content == content
        
        # Embedding should be None in file
        file_path = fs_memory_with_embeddings._get_user_memory_dir() / f"{artifact.id}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["embedding"] is None


class TestEmbeddingInitialization:
    """Test embedding provider initialization."""
    
    def test_filesystem_backend_init_with_embedding_provider(self, tmp_path, mock_embedding_provider):
        """Test FilesystemBackend initialization with embedding provider."""
        memory_dir = tmp_path / ".memory"
        memory_dir.mkdir()
        
        memory = FilesystemBackend(memory_dir=str(memory_dir), embedding_provider=mock_embedding_provider)
        assert memory.embedding_provider == mock_embedding_provider
    
    def test_filesystem_backend_init_without_embedding_provider(self, tmp_path):
        """Test FilesystemBackend initialization without embedding provider."""
        memory_dir = tmp_path / ".memory"
        memory_dir.mkdir()
        
        memory = FilesystemBackend(memory_dir=str(memory_dir))
        assert memory.embedding_provider is None