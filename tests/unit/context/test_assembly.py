"""Tests for context namespace API.

Tests define the expected context.assembly() interface for unified
context assembly with user-scoped data integration.
"""

import pytest

from cogency.context import context, working


def test_assemble_basic_context():
    """Assemble creates canonical message format without user data."""
    query = "What is 2 + 2?"
    user_id = "test_user"
    conversation_id = "conv_123"
    task_id = "task_123"

    result = context.assemble(query, user_id, conversation_id, task_id)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(msg, dict) for msg in result)
    assert all("role" in msg and "content" in msg for msg in result)
    assert result[0]["role"] == "system"
    assert result[-1]["content"] == query


def test_assemble_with_working_memory():
    """Assemble includes working memory in message format."""
    user_id = "working_test_user"
    task_id = "task_456"
    query = "Continue with the file operations"

    # Set up working memory
    tool_results = [
        {"tool": "file_write", "result": "Created test.txt"},
        {"tool": "file_read", "result": "Content: hello world"},
    ]
    working.update(task_id, tool_results)

    # Assemble should include working memory
    result = context.assemble(query, user_id, "conv_456", task_id)

    assert isinstance(result, list)
    assert len(result) >= 2  # system + query at minimum
    assert result[0]["role"] == "system"
    assert result[-1]["content"] == query


def test_assemble_user_isolation():
    """Assemble maintains user isolation in message format."""
    user_a = "user_a"
    user_b = "user_b"
    task_a = "task_a"
    task_b = "task_b"
    query = "Help me"

    # Set up different contexts for each user
    working.update(task_a, [{"tool": "model_train", "result": "Training complete"}])
    working.update(task_b, [{"tool": "server_start", "result": "Server running"}])

    context_a = context.assemble(query, user_a, "conv_a", task_a)
    context_b = context.assemble(query, user_b, "conv_b", task_b)

    # Contexts should be different and isolated
    assert context_a != context_b
    assert isinstance(context_a, list)
    assert isinstance(context_b, list)
    assert all("role" in msg for msg in context_a)
    assert all("role" in msg for msg in context_b)


def test_assemble_api_consistency():
    """Verify context namespace provides consistent API."""
    user_id = "api_test"
    query = "test"

    # Should work without error
    result = context.assemble(query, user_id, "conv_test", "task_test")

    # Verify the API is available
    assert hasattr(context, "assemble")
    assert callable(context.assemble)
    assert isinstance(result, list)


def test_assemble_empty_user_data():
    """Assemble handles users with no stored data gracefully."""
    user_id = "empty_user"
    query = "Simple question"

    # No memory or working data for this user
    result = context.assemble(query, user_id, "conv_empty", "task_empty")

    assert isinstance(result, list)
    assert len(result) >= 2  # system + query minimum
    assert result[-1]["content"] == query


def test_assemble_integrates_with_working():
    """Assemble properly integrates with working namespace."""
    user_id = "integration_test"
    task_id = "integration_task"
    query = "Continue task"

    # Use working namespace to set data
    tools = [{"tool": "test_tool", "result": "test_result"}]
    working.update(task_id, tools)

    # Assemble should access working data
    result = context.assemble(query, user_id, "conv_int", task_id)

    assert isinstance(result, list)
    assert result[-1]["content"] == query

    # Clean up
    working.clear(task_id)
    assert working.get(task_id) == []


def test_assemble_none_user_id():
    """Assemble handles None user_id gracefully."""
    with pytest.raises((ValueError, TypeError)):
        context.assemble("test", None, "conv_test", "task_test")


def test_assemble_empty_query():
    """Assemble handles empty query string."""
    result = context.assemble("", "test_user", "conv_test", "task_test")
    assert isinstance(result, list)
    assert result[-1]["content"] == ""
