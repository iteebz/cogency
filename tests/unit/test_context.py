"""Context tests."""

from cogency.context import Context


def test_creation():
    context = Context("test input")
    assert context.query == "test input"
    assert context.chat == []
    assert context.user_id == "default"


def test_history_management():
    context = Context("test", max_history=2)

    context.add_turn("user", "message 1")
    context.add_turn("assistant", "response 1")
    context.add_turn("user", "message 2")

    assert len(context.archive) == 2
    assert context.archive[0]["query"] == "assistant"
    assert context.archive[1]["query"] == "user"


def test_conversation_filtering():
    context = Context("test")

    context.add_turn("user", "regular user message")
    context.add_turn("assistant", "regular response")
    context.add_turn("assistant", '{"action": "tool_needed"}')
    context.add_turn("system", "system message")
    context.add_turn("assistant", "TOOL_CALL: calculator")

    clean = context.recent_turns()

    assert len(clean) == 2
    assert clean[0]["role"] == "user"
    assert clean[0]["content"] == "regular user message"
    assert clean[1]["role"] == "assistant"
    assert clean[1]["content"] == "regular response"


def test_tool_results():
    context = Context("test")

    context.add_result("calculator", {"x": 5, "y": 3}, {"result": 8})

    assert len(context.tool_log) == 1
    assert context.tool_log[0]["tool_name"] == "calculator"
    assert context.tool_log[0]["output"]["result"] == 8
