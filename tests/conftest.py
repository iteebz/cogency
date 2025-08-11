"""Shared test fixtures for cogency unit tests."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from cogency.state import State

# Import all fixtures from decomposed modules


@pytest.fixture
def temp_dir():
    """Temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def agent_state():
    """Basic agent state."""
    return State(query="test query")


@pytest.fixture
def temp_docs_dir():
    """Temporary directory with test documents for retrieval testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()

        # Create test documents
        (docs_dir / "readme.md").write_text(
            "# Project Documentation\nThis is a test project with authentication features."
        )
        (docs_dir / "auth.md").write_text(
            "# Authentication\nUsers can login with username and password. JWT tokens are used for sessions."
        )
        (docs_dir / "api.md").write_text(
            "# API Reference\nThe API supports rate limiting at 1000 requests per hour."
        )

        yield docs_dir


@pytest.fixture
def mock_embedder():
    """Mock embedding provider for testing."""
    embedder = Mock()
    embedder.embed = AsyncMock()
    return embedder
