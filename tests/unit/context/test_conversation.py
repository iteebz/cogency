"""Unit tests for conversation search functionality."""

from unittest.mock import patch

from cogency.context.conversation import ConversationHistory


def test_conversation_search_excludes_recent_messages():
    """Test search excludes recent messages to avoid overlap."""
    conversation = ConversationHistory()

    # 30 total messages, should exclude last 20, search first 10
    mock_messages = []
    for i in range(30):
        mock_messages.append(
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} about Python async programming",
            }
        )

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.search("test_user", "Python")

        # Should find matches only in first 10 messages (exclude recent 20)
        assert "historical matches" in result
        # Should contain early messages, not recent ones
        assert "Message 0" in result or "Message 1" in result
        assert "Message 25" not in result and "Message 29" not in result


def test_conversation_search_short_query():
    """Test search rejects short queries."""
    conversation = ConversationHistory()

    # Need sufficient messages to pass length check
    mock_messages = [{"role": "user", "content": f"msg {i}"} for i in range(25)]

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.search("test_user", "a")
        assert "Query too short" in result


def test_conversation_search_no_history():
    """Test search with no conversation history."""
    conversation = ConversationHistory()

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = []

        result = conversation.search("test_user", "test query")

        assert "No history" in result


def test_conversation_search_all_recent():
    """Test search when all messages are recent (no historical)."""
    conversation = ConversationHistory()

    # Only 15 messages, all excluded as recent
    mock_messages = []
    for i in range(15):
        mock_messages.append({"role": "user", "content": f"Recent message {i}"})

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.search("test_user", "message")

        assert "No historical messages" in result
        assert "all in current context" in result


def test_conversation_search_word_scoring():
    """Test search scores by word overlap."""
    conversation = ConversationHistory()

    # Messages with different relevance scores
    mock_messages = [
        {"role": "user", "content": "Python is great"},  # Score: 1
        {"role": "user", "content": "Python async programming in Python"},  # Score: 2
        {"role": "user", "content": "JavaScript is also good"},  # Score: 0
    ] + [{"role": "user", "content": f"padding {i}"} for i in range(20)]  # Recent padding

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.search("test_user", "Python")

        # Should find 2 matches, with higher scored message first
        assert "2 historical matches" in result
        assert "Python async programming" in result
        assert "Python is great" in result
        assert "JavaScript" not in result


def test_conversation_search_limits_results():
    """Test search limits to top 3 results."""
    conversation = ConversationHistory()

    # 10 matching messages + recent padding
    mock_messages = []
    for i in range(10):
        mock_messages.append(
            {"role": "user", "content": f"Python message {i} about async programming"}
        )
    # Add recent padding to exclude
    for i in range(20):
        mock_messages.append({"role": "user", "content": f"recent {i}"})

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.search("test_user", "Python")

        # Should find 10 matches but only show top 3
        assert "10 historical matches" in result
        assert result.count("[user]:") == 3
