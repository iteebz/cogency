"""Tests for advanced conversation CLI commands."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from cogency.cli.conversations import (
    archive_conversation,
    detailed_history,
    filter_conversations,
    search_conversations,
)


@pytest.mark.asyncio
async def test_search_conversations_no_results(capsys):
    """Test conversation search with no results."""
    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = []

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        await search_conversations("nonexistent")

    captured = capsys.readouterr()
    assert "No conversations to search" in captured.out


@pytest.mark.asyncio
async def test_search_conversations_title_match(capsys):
    """Test conversation search with title match."""
    from cogency.state import Conversation

    # Mock conversation data
    conversations = [
        {
            "conversation_id": "test-id-1234",
            "title": "Python programming help",
            "message_count": 5,
            "updated_at": datetime.now().isoformat(),
        }
    ]

    # Mock full conversation
    full_conv = Conversation(
        user_id="test",
        messages=[{"role": "user", "content": "How do I use Python?"}],
        last_updated=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations
    mock_store.load_conversation.return_value = full_conv

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        await search_conversations("python")

    captured = capsys.readouterr()
    assert "Found 1 conversations with matches" in captured.out
    assert "Python programming help" in captured.out
    assert "Title match" in captured.out


@pytest.mark.asyncio
async def test_search_conversations_content_match(capsys):
    """Test conversation search with content match."""
    from cogency.state import Conversation

    # Mock conversation data
    conversations = [
        {
            "conversation_id": "test-id-1234",
            "title": "General help",
            "message_count": 3,
            "updated_at": datetime.now().isoformat(),
        }
    ]

    # Mock full conversation with matching content
    full_conv = Conversation(
        user_id="test",
        messages=[
            {"role": "user", "content": "I need help with machine learning algorithms"},
            {"role": "assistant", "content": "I can help with ML algorithms"},
        ],
        last_updated=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations
    mock_store.load_conversation.return_value = full_conv

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        await search_conversations("machine learning")

    captured = capsys.readouterr()
    assert "Found 1 conversations with matches" in captured.out
    assert "content match" in captured.out
    assert "machine learning algorithms" in captured.out


@pytest.mark.asyncio
async def test_filter_conversations_no_filter(capsys):
    """Test conversation filter without specifying filter type."""
    await filter_conversations()

    captured = capsys.readouterr()
    assert "Available filters:" in captured.out
    assert "today" in captured.out
    assert "week" in captured.out
    assert "long" in captured.out


@pytest.mark.asyncio
async def test_filter_conversations_today(capsys):
    """Test filtering conversations by today."""
    # Mock conversation from today
    today_conv = {
        "conversation_id": "today-conv",
        "title": "Today's conversation",
        "message_count": 3,
        "updated_at": datetime.now().isoformat(),
    }

    # Mock conversation from yesterday
    yesterday_conv = {
        "conversation_id": "yesterday-conv",
        "title": "Yesterday's conversation",
        "message_count": 5,
        "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
    }

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = [today_conv, yesterday_conv]

    mock_session = AsyncMock()
    mock_session.get_conversation_id.return_value = None

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        with patch("cogency.cli.conversations.CLISession", return_value=mock_session):
            await filter_conversations("today")

    captured = capsys.readouterr()
    assert "filtered by today" in captured.out
    assert "1 of 2 conversations match" in captured.out
    assert "Today's conversation" in captured.out


@pytest.mark.asyncio
async def test_filter_conversations_long(capsys):
    """Test filtering long conversations."""
    # Mock long conversation
    long_conv = {
        "conversation_id": "long-conv",
        "title": "Long conversation",
        "message_count": 15,
        "updated_at": datetime.now().isoformat(),
    }

    # Mock short conversation
    short_conv = {
        "conversation_id": "short-conv",
        "title": "Short conversation",
        "message_count": 3,
        "updated_at": datetime.now().isoformat(),
    }

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = [long_conv, short_conv]

    mock_session = AsyncMock()
    mock_session.get_conversation_id.return_value = None

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        with patch("cogency.cli.conversations.CLISession", return_value=mock_session):
            await filter_conversations("long")

    captured = capsys.readouterr()
    assert "long conversations (10+ messages)" in captured.out
    assert "1 of 2 conversations match" in captured.out
    assert "Long conversation" in captured.out


@pytest.mark.asyncio
async def test_detailed_history(capsys):
    """Test detailed conversation history."""
    from cogency.state import Conversation

    # Mock conversation metadata
    conversations = [
        {
            "conversation_id": "test-conv-1234",
            "title": "Python help session",
            "message_count": 4,
            "updated_at": datetime.now().isoformat(),
        }
    ]

    # Mock full conversation
    full_conv = Conversation(
        user_id="test",
        messages=[
            {"role": "user", "content": "How do I learn Python effectively?"},
            {"role": "assistant", "content": "Start with basic syntax and practice daily..."},
            {"role": "user", "content": "What about data structures?"},
            {"role": "assistant", "content": "Focus on lists, dictionaries first..."},
        ],
        last_updated=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations
    mock_store.load_conversation.return_value = full_conv

    mock_session = AsyncMock()
    mock_session.get_conversation_id.return_value = None

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        with patch("cogency.cli.conversations.CLISession", return_value=mock_session):
            await detailed_history()

    captured = capsys.readouterr()
    assert "Detailed Conversation History" in captured.out
    assert "CONVERSATION test-con..." in captured.out
    assert "Python help session" in captured.out
    assert "Messages: 4" in captured.out
    assert "First: How do I learn Python effectively?" in captured.out
    assert "Last: Focus on lists, dictionaries first..." in captured.out


@pytest.mark.asyncio
async def test_archive_conversation_not_found(capsys):
    """Test archiving non-existent conversation."""
    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = []

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        await archive_conversation("nonexistent")

    captured = capsys.readouterr()
    assert "Conversation nonexist... not found" in captured.out


@pytest.mark.asyncio
async def test_archive_conversation_ambiguous_id(capsys):
    """Test archiving with ambiguous conversation ID."""
    # Mock multiple conversations with same prefix
    conversations = [
        {"conversation_id": "test-conv-1234", "title": "First conversation", "message_count": 3},
        {"conversation_id": "test-conv-5678", "title": "Second conversation", "message_count": 5},
    ]

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        await archive_conversation("test-conv")

    captured = capsys.readouterr()
    assert "Ambiguous ID 'test-conv' matches 2 conversations" in captured.out
    assert "First conversation" in captured.out
    assert "Second conversation" in captured.out


@pytest.mark.asyncio
async def test_archive_conversation_cancelled(capsys):
    """Test archiving conversation with user cancellation."""
    conversations = [
        {"conversation_id": "test-conv-1234", "title": "Test conversation", "message_count": 3}
    ]

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        with patch("builtins.input", return_value="n"):  # User cancels
            await archive_conversation("test-conv-1234")

    captured = capsys.readouterr()
    assert "Archiving conversation: test-con..." in captured.out
    assert "Test conversation" in captured.out
    assert "Archive cancelled" in captured.out


@pytest.mark.asyncio
async def test_archive_conversation_confirmed(capsys):
    """Test archiving conversation with user confirmation."""
    conversations = [
        {"conversation_id": "test-conv-1234", "title": "Test conversation", "message_count": 3}
    ]

    mock_store = AsyncMock()
    mock_store.list_conversations.return_value = conversations

    mock_session = AsyncMock()
    mock_session.get_conversation_id.return_value = "different-id"

    with patch("cogency.cli.conversations.SQLite", return_value=mock_store):
        with patch("cogency.cli.conversations.CLISession", return_value=mock_session):
            with patch("builtins.input", return_value="y"):  # User confirms
                await archive_conversation("test-conv-1234")

    captured = capsys.readouterr()
    assert "Archiving conversation: test-con..." in captured.out
    assert "Would archive conversation successfully" in captured.out
