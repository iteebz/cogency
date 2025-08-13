"""Integration tests for memory system E2E functionality."""

from cogency.storage import SQLite


async def test_memory_system_handles_storage_failures():
    """Test that memory system handles storage failures gracefully."""
    from unittest.mock import patch

    from cogency import Agent

    # Test with invalid database path to trigger storage failures
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test", memory=True)

        # Mock the storage to fail
        original_db_path = SQLite().db_path
        SQLite().db_path = "/invalid/path/database.db"

        try:
            # Should not crash on storage errors
            result = await agent.run_async("Test query", user_id="test_user")
            # Should still provide response even if memory operations fail
            assert result is not None
            assert len(result) > 0
        finally:
            # Restore original path
            SQLite().db_path = original_db_path
