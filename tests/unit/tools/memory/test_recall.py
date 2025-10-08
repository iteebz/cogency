from unittest.mock import MagicMock, patch

import pytest

from cogency.tools import Recall
from cogency.tools.memory.recall import MessageMatch


@pytest.fixture
def mock_sqlite():
    with patch("cogency.tools.memory.recall.sqlite3") as mock_lib:
        mock_conn = MagicMock()
        mock_lib.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        yield mock_conn


@pytest.mark.asyncio
async def test_recall_success(mock_sqlite):
    tool = Recall()
    # Mock _get_timestamps to return an empty list
    tool._get_timestamps = MagicMock(return_value=[])
    # Mock _search_messages to return a list of MessageMatch objects
    tool._search_messages = MagicMock(
        return_value=[
            MessageMatch(content="Hello world", timestamp=1678886400.0, conversation_id="conv1"),
            MessageMatch(
                content="Another message", timestamp=1678886300.0, conversation_id="conv2"
            ),
        ]
    )

    result = await tool.execute(query="hello", user_id="user1")

    assert not result.error
    assert result.outcome == "Memory searched for 'hello' (2 matches)"
    assert "Hello world" in result.content
    assert "Another message" in result.content
    tool._get_timestamps.assert_called_once_with(None)
    tool._search_messages.assert_called_once()


@pytest.mark.asyncio
async def test_recall_empty_query():
    tool = Recall()
    result = await tool.execute(query="", user_id="user1")

    assert result.error
    assert result.outcome == "Search query cannot be empty"


@pytest.mark.asyncio
async def test_recall_no_user_id():
    tool = Recall()
    result = await tool.execute(query="hello")

    assert result.error
    assert result.outcome == "User ID required for memory recall"


@pytest.mark.asyncio
async def test_recall_no_matches(mock_sqlite):
    tool = Recall()
    tool._get_timestamps = MagicMock(return_value=[])
    tool._search_messages = MagicMock(return_value=[])

    result = await tool.execute(query="nomatch", user_id="user1")

    assert not result.error
    assert result.outcome == "Memory searched for 'nomatch' (0 matches)"
    assert result.content == "No past references found outside current conversation"


@pytest.mark.asyncio
async def test_recall_excludes_current_conversation(mock_sqlite):
    tool = Recall()
    # Mock _get_timestamps to return one timestamp
    tool._get_timestamps = MagicMock(return_value=[1678886400.0])
    # Mock _search_messages to return one match, excluding the one from _get_timestamps
    tool._search_messages = MagicMock(
        return_value=[
            MessageMatch(
                content="Another message", timestamp=1678886300.0, conversation_id="conv2"
            ),
        ]
    )

    result = await tool.execute(query="hello", user_id="user1", conversation_id="conv1")

    assert not result.error
    assert result.outcome == "Memory searched for 'hello' (1 matches)"
    assert "Another message" in result.content
    tool._get_timestamps.assert_called_once_with("conv1")
    tool._search_messages.assert_called_once()


@pytest.mark.asyncio
async def test_recall_fuzzy_matching(mock_sqlite):
    tool = Recall()
    tool._get_timestamps = MagicMock(return_value=[])
    tool._search_messages = MagicMock(
        return_value=[
            MessageMatch(
                content="This is a test message", timestamp=1678886400.0, conversation_id="conv1"
            ),
        ]
    )

    result = await tool.execute(query="test message", user_id="user1")

    assert not result.error
    assert result.outcome == "Memory searched for 'test message' (1 matches)"
    assert "This is a test message" in result.content
