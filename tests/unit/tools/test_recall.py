"""Recall tool tests - memory search engine."""

import tempfile
from unittest.mock import patch

import pytest

from cogency.core.protocols import ToolResult
from cogency.lib.storage import save_message
from cogency.tools.memory.recall import MemoryRecall


def is_success(result):
    """Check if ToolResult indicates success."""
    failure_patterns = ["failed:", "error:", "Security violation:", "Tool execution failed:", "cannot be empty", "required"]
    return not any(pattern in result.outcome for pattern in failure_patterns)


@pytest.fixture
def recall_tool():
    return MemoryRecall()


@pytest.mark.asyncio
async def test_fuzzy_search_logic(recall_tool):
    """Fuzzy search finds relevant messages with keyword matching."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up test messages (conversation_id must match user_id pattern)
        await save_message(
            "user1_conv1", "user1", "user", "I love Python programming", temp_dir, 100
        )
        await save_message(
            "user1_conv1", "user1", "user", "Django is my favorite framework", temp_dir, 110
        )
        await save_message(
            "user1_conv1", "user1", "user", "Machine learning fascinates me", temp_dir, 120
        )
        await save_message(
            "user1_conv2", "user1", "user", "Java is also good for backend", temp_dir, 130
        )
        await save_message(
            "user2_conv1", "user2", "user", "I prefer React for frontend", temp_dir, 140
        )

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Search for programming-related content
            result = await recall_tool.execute("Python programming", user_id="user1")

            assert isinstance(result, ToolResult)
            assert "Python programming" in result.content
            assert "1 matches" in result.outcome

            # Search for broader term
            result = await recall_tool.execute("programming", user_id="user1")

            assert not any(failure in result.outcome for failure in ["failed:", "error:", "Security violation:"])
            assert "Python programming" in result.content


@pytest.mark.asyncio
async def test_context_exclusion(recall_tool):
    """Current conversation messages are excluded from search results."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Messages in current conversation (should be excluded)
        await save_message("user1_current", "user1", "user", "Python is great for AI", temp_dir, 200)
        await save_message("user1_current", "user1", "user", "Django works well too", temp_dir, 210)

        # Messages in past conversations (should be found)
        await save_message("user1_old1", "user1", "user", "Python was my first language", temp_dir, 100)
        await save_message("user1_old2", "user1", "user", "Still love Python today", temp_dir, 110)

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Mock current conversation context
            with patch.object(recall_tool, "_get_timestamps", return_value=[200.0, 210.0]):
                result = await recall_tool.execute(
                    "Python", conversation_id="user1_current", user_id="user1"
                )

                assert is_success(result)
                content = result.content
                # Should find old messages, not current ones
                assert "first language" in content or "Still love" in content
                assert "great for AI" not in content
                assert "Django works" not in content


@pytest.mark.asyncio
async def test_user_isolation(recall_tool):
    """Search results are isolated by user."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # User1 messages
        await save_message("user1_conv1", "user1", "user", "I work with Python daily", temp_dir, 100)
        await save_message("user1_conv2", "user1", "user", "Python is my go-to language", temp_dir, 110)

        # User2 messages
        await save_message(
            "user2_conv1", "user2", "user", "Python seems complicated to me", temp_dir, 120
        )
        await save_message(
            "user2_conv2", "user2", "user", "Maybe Python isn't for everyone", temp_dir, 130
        )

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            # Search as user1
            result = await recall_tool.execute("Python", user_id="user1")

            assert is_success(result)
            content = result.content
            assert "work with Python" in content or "go-to language" in content
            assert "complicated" not in content
            assert "isn't for everyone" not in content


@pytest.mark.asyncio
async def test_relevance_ranking(recall_tool):
    """Results are ranked by relevance (keyword frequency)."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Message with multiple keyword matches (should rank higher)
        await save_message(
            "user1_conv1",
            "user1",
            "user",
            "Python Python Python is the best language",
            temp_dir,
            100,
        )
        # Message with single keyword match
        await save_message("user1_conv2", "user1", "user", "I like Python for scripting", temp_dir, 110)

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            result = await recall_tool.execute("Python", user_id="user1")

            assert is_success(result)
            content = result.content
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
            assert not is_success(result)
            assert "cannot be empty" in result.outcome

            # Missing user_id
            result = await recall_tool.execute("test query")
            assert not is_success(result)
            assert "User ID required" in result.outcome

            # No matches found
            result = await recall_tool.execute("nonexistent", user_id="user1")
            assert is_success(result)
            assert "No past references found" in result.content


@pytest.mark.asyncio
async def test_result_formatting(recall_tool):
    """Results are properly formatted with timestamps."""

    with tempfile.TemporaryDirectory() as temp_dir:
        await save_message("user1_conv1", "user1", "user", "Short message", temp_dir, 100)
        await save_message(
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

            assert is_success(result)
            content = result.content
            lines = content.split("\n")

            # Should have relative timestamps (format: "55y: message")
            assert any(":" in line for line in lines)
            # Long message should be truncated
            assert any("..." in line for line in lines)
            # Should have both messages
            assert len(lines) == 2
