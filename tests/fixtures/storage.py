"""Storage and database fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_storage():
    """Auto-mock storage functional operations for fast tests."""
    with (
        patch("cogency.storage.sqlite.save_knowledge_vector") as mock_save_knowledge,
        patch("cogency.storage.sqlite.save_profile") as mock_save_profile,
        patch("cogency.storage.sqlite.load_profile") as mock_load_profile,
        patch("cogency.storage.sqlite.save_conversation") as mock_save_conv,
        patch("cogency.storage.sqlite.load_conversation") as mock_load_conv,
    ):
        # Mock all storage operations as successful
        mock_save_knowledge.return_value = AsyncMock()
        mock_save_profile.return_value = AsyncMock()
        mock_load_profile.return_value = AsyncMock(return_value=None)
        mock_save_conv.return_value = AsyncMock()
        mock_load_conv.return_value = AsyncMock(return_value=None)

        yield {
            "save_knowledge": mock_save_knowledge,
            "save_profile": mock_save_profile,
            "load_profile": mock_load_profile,
            "save_conversation": mock_save_conv,
            "load_conversation": mock_load_conv,
        }


@pytest.fixture
async def temp_db():
    """Temporary database for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        # TODO: Replace with functional SQLite operations when integration tests are updated
        yield str(db_path)
