"""Storage and database fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_storage():
    """Auto-mock storage to use in-memory instead of real databases."""
    with patch("cogency.storage.sqlite.SQLite") as mock_sqlite:
        mock_instance = Mock()
        mock_instance._ensure_schema = AsyncMock()
        mock_instance.save_knowledge = AsyncMock()
        mock_instance.save_profile = AsyncMock()
        mock_instance.init = AsyncMock()
        mock_instance.close = AsyncMock()
        mock_sqlite.return_value = mock_instance

        yield mock_instance


@pytest.fixture
async def temp_db():
    """Temporary database for integration tests."""
    from cogency.storage.sqlite import SQLite

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLite(str(db_path))

        await storage.init()
        yield storage
        await storage.close()
