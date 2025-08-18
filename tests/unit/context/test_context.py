"""Context tests."""

from cogency.context import context, conversation, knowledge, system, working


def test_system():
    """System context."""
    result = system()
    assert isinstance(result, str)
    assert len(result) > 0


def test_conversation():
    """Conversation context."""
    result = conversation("test")
    assert isinstance(result, str)


def test_knowledge():
    """Knowledge context."""
    result = knowledge("test", "test")
    assert isinstance(result, str)


def test_working():
    """Working context."""
    result = working()
    assert result == ""

    tools = [{"tool": "test", "result": "ok", "iteration": 1}]
    result = working(tools)
    assert isinstance(result, str)
    assert "test" in result


def test_context():
    """Context assembly."""
    ctx = context("test", "test")
    assert isinstance(ctx, str)
    assert "assistant" in ctx.lower() or "helpful" in ctx.lower()


def test_context_tools():
    """Context with tools."""
    tools = [{"tool": "read", "result": "content", "iteration": 1}]
    ctx = context("test", "test", tools)
    assert isinstance(ctx, str)
    assert "read" in ctx
