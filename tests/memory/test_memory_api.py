"""Test Memory API - magical backend auto-configuration."""

from unittest.mock import Mock, patch

import pytest

from cogency.memory.api import Memory
from cogency.memory.core import MemoryBackend


class MockBackend(MemoryBackend):
    """Mock backend for testing."""

    def __init__(self, **config):
        super().__init__()
        self.config = config

    async def create(self, content, memory_type=None, tags=None, metadata=None, **kwargs):
        pass

    async def read(
        self,
        query=None,
        artifact_id=None,
        search_type=None,
        limit=10,
        threshold=0.7,
        tags=None,
        memory_type=None,
        filters=None,
        **kwargs,
    ):
        pass

    async def update(self, artifact_id, updates):
        pass

    async def delete(self, artifact_id=None, tags=None, filters=None, delete_all=False):
        pass


class TestMemoryAPI:
    """Test Memory factory interface."""

    @patch("cogency.memory.backends.get_backend")
    def test_create_backend_default(self, mock_get_backend):
        # Setup
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get_backend.return_value = mock_backend_class

        # Execute
        backend = Memory.create()

        # Verify
        mock_get_backend.assert_called_once_with("filesystem")
        mock_backend_class.assert_called_once_with()
        assert isinstance(backend, MockBackend)

    @patch("cogency.memory.backends.get_backend")
    def test_create_backend_custom(self, mock_get_backend):
        # Setup
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get_backend.return_value = mock_backend_class

        # Execute
        backend = Memory.create("chroma", host="localhost", port=8000)

        # Verify
        mock_get_backend.assert_called_once_with("chroma")
        mock_backend_class.assert_called_once_with(host="localhost", port=8000)
        assert isinstance(backend, MockBackend)

    @patch("cogency.memory.backends.list_backends")
    def test_list_backends(self, mock_list_backends):
        # Setup
        expected_backends = ["filesystem", "chroma", "pinecone", "postgres"]
        mock_list_backends.return_value = expected_backends

        # Execute
        backends = Memory.list_backends()

        # Verify
        mock_list_backends.assert_called_once()
        assert backends == expected_backends

    @patch("cogency.memory.backends.get_backend")
    def test_create_with_embedder(self, mock_get_backend):
        # Setup
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get_backend.return_value = mock_backend_class
        mock_embedding = Mock()

        # Execute
        Memory.create("chroma", embedder=mock_embedding)

        # Verify
        mock_get_backend.assert_called_once_with("chroma")
        mock_backend_class.assert_called_once_with(embedder=mock_embedding)

    @patch("cogency.memory.backends.get_backend")
    def test_create_backend_not_found(self, mock_get_backend):
        # Setup
        mock_get_backend.side_effect = ValueError("Backend 'invalid' not found")

        # Execute & Verify
        with pytest.raises(ValueError, match="Backend 'invalid' not found"):
            Memory.create("invalid")

        mock_get_backend.assert_called_once_with("invalid")


class TestMemoryIntegration:
    """Test Memory API integration patterns."""

    @patch("cogency.memory.backends.get_backend")
    def test_magical_creation_pattern(self, mock_get_backend):
        """Test the magical auto-configuration pattern."""
        # Setup
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get_backend.return_value = mock_backend_class

        # Execute - zero ceremony creation
        memory = Memory.create()

        # Verify magical behavior
        assert memory is not None
        assert isinstance(memory, MemoryBackend)
        mock_get_backend.assert_called_once_with("filesystem")  # Default backend

    @patch("cogency.memory.backends.get_backend")
    @patch("cogency.memory.backends.list_backends")
    def test_discovery_integration(self, mock_list, mock_get):
        """Test backend discovery works with creation."""
        # Setup
        mock_list.return_value = ["filesystem", "chroma"]
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get.return_value = mock_backend_class

        # Execute
        available = Memory.list_backends()
        Memory.create(available[0])

        # Verify
        assert len(available) == 2
        assert "filesystem" in available
        mock_get.assert_called_once_with("filesystem")

    @patch("cogency.memory.backends.get_backend")
    def test_config_passthrough(self, mock_get_backend):
        """Test configuration parameters pass through correctly."""
        # Setup
        mock_backend_class = Mock(return_value=MockBackend())
        mock_get_backend.return_value = mock_backend_class

        config = {
            "host": "localhost",
            "port": 5432,
            "database": "memory_db",
            "embedder": Mock(),
        }

        # Execute
        Memory.create("postgres", **config)

        # Verify all config passed through
        mock_get_backend.assert_called_once_with("postgres")
        mock_backend_class.assert_called_once_with(**config)
