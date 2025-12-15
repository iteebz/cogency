from unittest.mock import AsyncMock

import pytest

from cogency.lib.sqlite import MessageMatch
from cogency.tools import Recall


@pytest.fixture
def mock_storage():
    mock = AsyncMock()
    mock.load_messages_by_conversation_id.return_value = []
    mock.search_messages.return_value = []
    return mock


@pytest.mark.asyncio
async def test_finds_matches(mock_storage):
    tool = Recall
    mock_storage.load_messages_by_conversation_id.return_value = []
    mock_storage.search_messages.return_value = [
        MessageMatch(content="Hello world", timestamp=1678886400.0, conversation_id="conv1"),
        MessageMatch(content="Another message", timestamp=1678886300.0, conversation_id="conv2"),
    ]

    result = await tool.execute(query="hello", user_id="user1", storage=mock_storage)

    assert not result.error
    assert result.outcome == "Memory searched for 'hello' (2 matches)"
    assert result.content is not None
    assert "Hello world" in result.content
    assert "Another message" in result.content
    mock_storage.load_messages_by_conversation_id.assert_called_once_with(
        conversation_id="", limit=20
    )
    mock_storage.search_messages.assert_called_once_with(
        query="hello", user_id="user1", exclude_timestamps=[], limit=3
    )


@pytest.mark.asyncio
async def test_empty_query(mock_storage):
    tool = Recall
    result = await tool.execute(query="", user_id="user1", storage=mock_storage)

    assert result.error
    assert result.outcome == "Search query cannot be empty"


@pytest.mark.asyncio
async def test_no_user_id(mock_storage):
    tool = Recall
    result = await tool.execute(query="hello", storage=mock_storage)

    assert result.error
    assert result.outcome == "User ID required for memory recall"


@pytest.mark.asyncio
async def test_no_matches(mock_storage):
    tool = Recall
    mock_storage.load_messages_by_conversation_id.return_value = []
    mock_storage.search_messages.return_value = []

    result = await tool.execute(query="nomatch", user_id="user1", storage=mock_storage)

    assert not result.error
    assert result.outcome == "Memory searched for 'nomatch' (0 matches)"
    assert result.content == "No past references found outside current conversation"
    mock_storage.load_messages_by_conversation_id.assert_called_once_with(
        conversation_id="", limit=20
    )
    mock_storage.search_messages.assert_called_once_with(
        query="nomatch", user_id="user1", exclude_timestamps=[], limit=3
    )


@pytest.mark.asyncio
async def test_excludes_current_conversation(mock_storage):
    tool = Recall
    mock_storage.load_messages_by_conversation_id.return_value = [
        {"timestamp": 1678886400.0, "content": "test"}
    ]
    mock_storage.search_messages.return_value = [
        MessageMatch(content="Another message", timestamp=1678886300.0, conversation_id="conv2"),
    ]

    result = await tool.execute(
        query="hello", user_id="user1", conversation_id="conv1", storage=mock_storage
    )

    assert not result.error
    assert result.outcome == "Memory searched for 'hello' (1 matches)"
    assert result.content is not None
    assert "Another message" in result.content
    mock_storage.load_messages_by_conversation_id.assert_called_once_with(
        conversation_id="conv1", limit=20
    )
    mock_storage.search_messages.assert_called_once_with(
        query="hello", user_id="user1", exclude_timestamps=[1678886400.0], limit=3
    )


@pytest.mark.asyncio
async def test_fuzzy_matching(mock_storage):
    tool = Recall
    mock_storage.load_messages_by_conversation_id.return_value = []
    mock_storage.search_messages.return_value = [
        MessageMatch(
            content="This is a test message", timestamp=1678886400.0, conversation_id="conv1"
        ),
    ]

    result = await tool.execute(query="test message", user_id="user1", storage=mock_storage)

    assert not result.error
    assert result.outcome == "Memory searched for 'test message' (1 matches)"
    assert result.content is not None
    assert "This is a test message" in result.content
    mock_storage.load_messages_by_conversation_id.assert_called_once_with(
        conversation_id="", limit=20
    )
    mock_storage.search_messages.assert_called_once_with(
        query="test message", user_id="user1", exclude_timestamps=[], limit=3
    )
