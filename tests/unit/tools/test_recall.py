"""Recall tool tests - memory search engine."""

import tempfile
from unittest.mock import patch

import pytest

from cogency.lib.storage import save_message
from cogency.tools.memory.recall import MemoryRecall


@pytest.fixture
def recall_tool():
    return MemoryRecall()


@pytest.mark.asyncio
async def test_fuzzy_search_logic(recall_tool):
    """Fuzzy search finds relevant messages with keyword matching."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up test messages (conversation_id must match user_id pattern)
        save_message("user1_conv1", "user1", "user", "I love Python programming", temp_dir, 100)
        save_message(
            "user1_conv1", "user1", "user", "Django is my favorite framework", temp_dir, 110
        )
        save_message(
            "user1_conv1", "user1", "user", "Machine learning fascinates me", temp_dir, 120
        )
        save_message("user1_conv2", "user1", "user", "Java is also good for backend", temp_dir, 130)
        save_message("user2_conv1", "user2", "user", "I prefer React for frontend", temp_dir, 140)

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Search for programming-related content
            result = await recall_tool.execute("Python programming", user_id="user1")

            assert result.success
            assert "Python programming" in result.unwrap().content
            assert "1 matches" in result.unwrap().outcome

            # Search for broader term
            result = await recall_tool.execute("programming", user_id="user1")

            assert result.success
            content = result.unwrap().content
            assert "Python programming" in content


@pytest.mark.asyncio
async def test_context_exclusion(recall_tool):
    """Current conversation messages are excluded from search results."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Messages in current conversation (should be excluded)
        save_message("user1_current", "user1", "user", "Python is great for AI", temp_dir, 200)
        save_message("user1_current", "user1", "user", "Django works well too", temp_dir, 210)

        # Messages in past conversations (should be found)
        save_message("user1_old1", "user1", "user", "Python was my first language", temp_dir, 100)
        save_message("user1_old2", "user1", "user", "Still love Python today", temp_dir, 110)

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Mock current conversation context
            with patch.object(recall_tool, "_get_timestamps", return_value=[200.0, 210.0]):
                result = await recall_tool.execute(
                    "Python", conversation_id="user1_current", user_id="user1"
                )

                assert result.success
                content = result.unwrap().content
                # Should find old messages, not current ones
                assert "first language" in content or "Still love" in content
                assert "great for AI" not in content
                assert "Django works" not in content


@pytest.mark.asyncio
async def test_user_isolation(recall_tool):
    """Search results are isolated by user."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # User1 messages
        save_message("user1_conv1", "user1", "user", "I work with Python daily", temp_dir, 100)
        save_message("user1_conv2", "user1", "user", "Python is my go-to language", temp_dir, 110)

        # User2 messages
        save_message(
            "user2_conv1", "user2", "user", "Python seems complicated to me", temp_dir, 120
        )
        save_message(
            "user2_conv2", "user2", "user", "Maybe Python isn't for everyone", temp_dir, 130
        )

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Search as user1
            result = await recall_tool.execute("Python", user_id="user1")

            assert result.success
            content = result.unwrap().content
            assert "work with Python" in content or "go-to language" in content
            assert "complicated" not in content
            assert "isn't for everyone" not in content


@pytest.mark.asyncio
async def test_relevance_ranking(recall_tool):
    """Results are ranked by relevance (keyword frequency)."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Message with multiple keyword matches (should rank higher)
        save_message(
            "user1_conv1",
            "user1",
            "user",
            "Python Python Python is the best language",
            temp_dir,
            100,
        )
        # Message with single keyword match
        save_message("user1_conv2", "user1", "user", "I like Python for scripting", temp_dir, 110)

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            result = await recall_tool.execute("Python", user_id="user1")

            assert result.success
            content = result.unwrap().content
            lines = content.split("\n")
            # First result should be the one with more keyword matches
            assert "best language" in lines[0]


@pytest.mark.asyncio
async def test_edge_cases(recall_tool):
    """Handles edge cases gracefully."""

    with tempfile.TemporaryDirectory() as temp_dir:
        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Empty query
            result = await recall_tool.execute("", user_id="user1")
            assert not result.success
            assert "cannot be empty" in result.error

            # Missing user_id
            result = await recall_tool.execute("test query")
            assert not result.success
            assert "User ID required" in result.error

            # No matches found
            result = await recall_tool.execute("nonexistent", user_id="user1")
            assert result.success
            assert "No past references found" in result.unwrap().content


@pytest.mark.asyncio
async def test_result_formatting(recall_tool):
    """Results are properly formatted with timestamps."""

    with tempfile.TemporaryDirectory() as temp_dir:
        save_message("user1_conv1", "user1", "user", "Short message", temp_dir, 100)
        save_message(
            "user1_conv2",
            "user1",
            "user",
            "This is a very long message that should be truncated because it exceeds the maximum length limit for display purposes",
            temp_dir,
            110,
        )

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            result = await recall_tool.execute("message", user_id="user1")

            assert result.success
            content = result.unwrap().content
            lines = content.split("\n")

            # Should have relative timestamps (format: "55y: message")
            assert any(":" in line for line in lines)
            # Long message should be truncated
            assert any("..." in line for line in lines)
            # Should have both messages
            assert len(lines) == 2
