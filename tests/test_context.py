"""Context tests."""

from cogency.context import context, conversation, knowledge, memory, system, working


def test_system():
    result = system()
    assert isinstance(result, str)
    assert len(result) > 0


def test_conversation():
    result = conversation("test")
    assert isinstance(result, list)
    
    # Test contract: nonexistent user returns empty list
    result = conversation("nonexistent_user_12345")
    assert isinstance(result, list)
    assert result == []


def test_knowledge():
    result = knowledge("test", "test")
    assert isinstance(result, str)


def test_memory():
    result = memory("test")
    assert isinstance(result, str)


def test_working():
    result = working()
    assert result == ""

    tools = [{"tool": "test", "result": "ok", "iteration": 1}]
    result = working(tools)
    assert isinstance(result, str)
    assert "test" in result


def test_assembly():
    ctx = context("python tutorial", "test_user")

    assert len(ctx) >= 1
    assert ctx[0]["role"] == "system"
    assert "helpful" in ctx[0]["content"].lower()

    from cogency.tools import FileRead
    tools = [FileRead()]
    ctx_with_tools = context("debug this", "test_user", tools)

    assert "file_read" in ctx_with_tools[0]["content"].lower()
    assert "read" in ctx_with_tools[0]["content"].lower()
