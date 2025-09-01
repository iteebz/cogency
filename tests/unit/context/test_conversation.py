"""Conversation history tests - History logic and formatting."""

from unittest.mock import patch

from cogency.context.constants import DEFAULT_CONVERSATION_ID, HISTORY_LIMIT
from cogency.context.conversation import history
from cogency.core.protocols import Event


def test_limit_20():
    """Verify exactly 20 DB rows used for history."""
    # Create 30 past messages (before current user message)
    past_messages = [
        msg
        for i in range(15)
        for msg in [
            {"type": Event.USER, "content": f"Query {i}"},
            {"type": "respond", "content": f"Response {i}"},
        ]
    ]
    # Add current user message
    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]

    with patch("cogency.context.conversation.load_messages", return_value=all_messages):
        result = history("conv_123")

        # Count lines in result (should be exactly HISTORY_LIMIT)
        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) == HISTORY_LIMIT


@patch("cogency.context.conversation.load_messages")
def test_chronological(mock_load):
    """Verify USER → TOOLS → ASSISTANT order in history."""
    # Create messages with proper chronological flow
    past_messages = [
        {"type": Event.USER, "content": "First query"},
        {
            "type": Event.CALLS,
            "content": '[{"call": {"name": "test", "args": {}}, "result": "OK"}]',
        },
        {"type": Event.RESPOND, "content": "First response"},
        {"type": Event.USER, "content": "Second query"},
        {
            "type": Event.CALLS,
            "content": '[{"call": {"name": "test2", "args": {}}, "result": "OK"}]',
        },
        {"type": Event.RESPOND, "content": "Second response"},
    ]
    # Add current user message (excluded from history)
    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]

    mock_load.return_value = all_messages

    with patch("cogency.lib.format.format_tools", return_value="TOOLS_FORMATTED"):
        result = history("conv_123")

        lines = [line.strip() for line in result.split("\n") if line.strip()]

        # Verify chronological order pattern
        expected_pattern = [
            "USER: First query",
            "TOOLS: TOOLS_FORMATTED",
            "ASSISTANT: First response",
            "USER: Second query",
            "TOOLS: TOOLS_FORMATTED",
            "ASSISTANT: Second response",
        ]

        assert lines == expected_pattern


@patch("cogency.context.conversation.load_messages")
def test_filter_think(mock_load):
    """Verify 'think' messages filtered before history limit."""
    past_messages = [
        {"type": Event.USER, "content": "Query"},
        {"type": Event.THINK, "content": "I need to think about this..."},  # Should be filtered
        {"type": "assistant", "content": "Response"},
    ]
    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]

    mock_load.return_value = all_messages

    result = history("conv_123")

    # Verify thinking content is not in history
    assert "I need to think about this" not in result


@patch("cogency.context.conversation.load_messages")
def test_tools_truncate(mock_load):
    """Verify tools use format_tools with truncate=True."""
    past_messages = [
        {"type": Event.USER, "content": "Query"},
        {"type": Event.CALLS, "content": '[{"name": "test", "args": {"long": "data"}}]'},
        {"type": Event.RESULTS, "content": '["Long result"]'},
    ]
    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]

    mock_load.return_value = all_messages

    with patch("cogency.lib.format.format_tools", return_value="TRUNCATED_TOOLS") as mock_format:
        result = history("conv_123")

        # Verify format_tools was called with truncate=True
        mock_format.assert_called_with(
            '[{"call": {"name": "test", "args": {"long": "data"}}, "result": "Long result"}]',
            truncate=True,
        )

        # Verify truncated version appears in result
        assert "TOOLS: TRUNCATED_TOOLS" in result


@patch("cogency.context.conversation.load_messages")
def test_off_by_one(mock_load):
    """Verify current cycle never appears in history."""
    past_messages = [
        {"type": Event.USER, "content": "Past query"},
        {"type": "assistant", "content": "Past response"},
    ]
    current_cycle = [
        {"type": Event.USER, "content": "Current query"},
        {"type": Event.THINK, "content": "Current thinking"},
        {"type": Event.CALLS, "content": "Current tools"},
    ]
    all_messages = past_messages + current_cycle

    mock_load.return_value = all_messages

    result = history("conv_123")

    # Verify current cycle content is NOT in history
    assert "Current query" not in result
    assert "Current thinking" not in result
    assert "Current tools" not in result

    # Verify past content IS in history
    assert "Past query" in result
    assert "Past response" in result


@patch("cogency.context.conversation.load_messages")
def test_tools_count_one(mock_load):
    """Verify 3 tool calls count as 1 message, not 6."""
    past_messages = [
        {"type": Event.USER, "content": "Query"},
        {
            "type": Event.CALLS,
            "content": '[{"call": {"name": "tool1", "args": {}}, "result": "OK1"}, {"call": {"name": "tool2", "args": {}}, "result": "OK2"}, {"call": {"name": "tool3", "args": {}}, "result": "OK3"}]',
        },
    ]
    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]

    mock_load.return_value = all_messages

    with patch("cogency.lib.format.format_tools", return_value="3 tools executed"):
        result = history("conv_123")

        lines = [line.strip() for line in result.split("\n") if line.strip()]

        # Should be 2 lines: USER + TOOLS (not 6 lines)
        assert len(lines) == 2
        assert lines[0] == "USER: Query"
        assert lines[1] == "TOOLS: 3 tools executed"


def test_limit_constant():
    """Verify HISTORY_LIMIT = 20 exists."""
    assert HISTORY_LIMIT == 20


def test_default_id():
    """Verify DEFAULT_CONVERSATION_ID exists."""
    assert DEFAULT_CONVERSATION_ID == "ephemeral"


def test_ephemeral_empty():
    """Verify ephemeral conversation returns empty history."""
    result = history(DEFAULT_CONVERSATION_ID)
    assert result == ""


def test_nonexistent_empty():
    """Verify non-existent conversation returns empty history."""
    result = history("nonexistent")
    assert result == ""


@patch("cogency.context.conversation.load_messages")
def test_think_filter_first(mock_load):
    """Verify 'think' messages filtered BEFORE history limit, not after."""
    # Create scenario with many think messages that would break old logic:
    # 25 total messages: 15 think + 10 conversational + 1 current
    # OLD BUG: Take last 20 DB rows (15 think + 5 conversational) -> 5 history lines
    # NEW FIX: Filter thinks first (10 conversational) -> all 10 history lines
    past_messages = []
    for i in range(5):
        past_messages.extend(
            [
                {"type": Event.USER, "content": f"Query {i}"},
                {"type": Event.THINK, "content": f"Think {i}a"},
                {"type": Event.THINK, "content": f"Think {i}b"},
                {"type": Event.THINK, "content": f"Think {i}c"},
                {"type": "assistant", "content": f"Response {i}"},
            ]
        )

    all_messages = past_messages + [{"type": Event.USER, "content": "Current query"}]
    mock_load.return_value = all_messages

    result = history("conv_123")
    lines = [line.strip() for line in result.split("\n") if line.strip()]

    # Should get all 10 conversational messages (5 USER + 5 ASSISTANT)
    # NOT truncated by the 15 think messages
    assert len(lines) == 10
    assert lines[0] == "USER: Query 0"
    assert lines[-1] == "ASSISTANT: Response 4"

    # Verify no think content leaked through
    for line in lines:
        assert "Think" not in line
