"""Test Memory API - magical backend auto-configuration."""

import pytest

from cogency.memory import FilesystemBackend, Store
from cogency.memory.api import Memory


class TestMemoryAPI:
    def test_create_backend_default(self):
        """Test that default filesystem backend is created."""
        backend = Memory.create()

        assert isinstance(backend, Store)
        # FileBackend should be the default
        assert backend.__class__.__name__ == "FileBackend"

    def test_create_backend_custom_config(self):
        """Test backend creation with custom config."""
        backend = Memory.create("filesystem", memory_dir="/tmp/test")

        assert isinstance(backend, Store)
        assert backend.__class__.__name__ == "FileBackend"
        # Config should be passed through
        assert hasattr(backend, "memory_dir")

    def test_list_backends(self):
        """Test that available backends are listed."""
        backends = Memory.list_backends()

        expected_backends = ["filesystem", "postgres", "chroma", "pinecone"]
        assert set(backends) == set(expected_backends)

    def test_create_backend_not_found(self):
        """Test error handling for unknown backends."""
        with pytest.raises(ValueError, match="Unknown backend: invalid"):
            Memory.create("invalid")

    def test_magical_creation_pattern(self):
        """Test the zero-ceremony creation pattern."""
        # Should work with no arguments
        memory = Memory.create()
        assert memory is not None
        assert isinstance(memory, Store)

    def test_config_passthrough(self):
        """Test that configuration is passed through correctly."""
        # Test with embedder config
        from unittest.mock import Mock

        mock_embedder = Mock()

        backend = Memory.create("filesystem", embedder=mock_embedder)
        assert backend.embedder == mock_embedder


class TestStoreTypes:
    """Test that different backend types can be instantiated."""

    def test_filesystem_backend(self):
        """Test FileBackend creation."""
        backend = Memory.create("filesystem")
        assert backend.__class__.__name__ == "FileBackend"

    def test_postgres_backend(self):
        """Test PGVectorBackend creation."""
        backend = Memory.create("postgres", connection_string="postgresql://test")
        assert backend.__class__.__name__ == "PGVectorBackend"

    def test_chroma_backend(self):
        """Test ChromaBackend creation."""
        backend = Memory.create("chroma")
        assert backend.__class__.__name__ == "ChromaBackend"

    def test_pinecone_backend(self):
        """Test PineconeBackend creation."""
        backend = Memory.create("pinecone", api_key="test", index_name="test")
        assert backend.__class__.__name__ == "PineconeBackend"
