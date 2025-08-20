"""Unit tests for tool execution functions."""

from unittest.mock import AsyncMock

import pytest

from cogency.core.execute import execute_tools
from cogency.lib.result import Err, Ok


@pytest.fixture
def mock_tools():
    """Mock tools with different execution behaviors."""
    file_write = AsyncMock()
    file_write.name = "file_write"
    file_write.execute.return_value = Ok("File written successfully")

    search = AsyncMock()
    search.name = "search"
    search.execute.return_value = Ok("Search results found")

    failing_tool = AsyncMock()
    failing_tool.name = "failing_tool"
    failing_tool.execute.return_value = Err("Tool execution failed")

    return {
        "file_write": file_write,
        "search": search,
        "failing_tool": failing_tool,
    }


@pytest.mark.asyncio
async def test_execute_single_tool(mock_tools):
    """Test executing a single tool."""
    tools_json = '[{"name": "file_write", "args": {"filename": "test.txt", "content": "hello"}}]'

    result = await execute_tools("task123", tools_json, mock_tools)

    assert result.success
    mock_tools["file_write"].execute.assert_called_once_with(filename="test.txt", content="hello")


@pytest.mark.asyncio
async def test_execute_multiple_tools_sequential(mock_tools):
    """Test executing multiple tools sequentially."""
    tools_json = """[
        {"name": "file_write", "args": {"filename": "test.txt", "content": "hello"}},
        {"name": "search", "args": {"query": "python tutorial"}}
    ]"""

    result = await execute_tools("task123", tools_json, mock_tools)

    assert result.success
    mock_tools["file_write"].execute.assert_called_once_with(filename="test.txt", content="hello")
    mock_tools["search"].execute.assert_called_once_with(query="python tutorial")


@pytest.mark.asyncio
async def test_execute_tools_propagates_failure(mock_tools):
    """Test that first tool failure stops execution."""
    tools_json = """[
        {"name": "failing_tool", "args": {}},
        {"name": "search", "args": {"query": "test"}}
    ]"""

    result = await execute_tools("task123", tools_json, mock_tools)

    assert result.failure
    assert "Tool failing_tool failed" in result.error
    # Second tool should not be called due to failure propagation
    mock_tools["search"].execute.assert_not_called()


@pytest.mark.asyncio
async def test_execute_empty_tools_array(mock_tools):
    """Test executing empty tools array."""
    result = await execute_tools("task123", "[]", mock_tools)

    assert result.success


@pytest.mark.asyncio
async def test_execute_invalid_json(mock_tools):
    """Test executing invalid JSON."""
    result = await execute_tools("task123", '{"invalid": json}', mock_tools)

    assert result.failure
    assert "Invalid JSON" in result.error


@pytest.mark.asyncio
async def test_execute_unknown_tool(mock_tools):
    """Test executing unknown tool."""
    tools_json = '[{"name": "unknown_tool", "args": {}}]'

    result = await execute_tools("task123", tools_json, mock_tools)

    assert result.failure
    assert "Unknown tool: unknown_tool" in result.error


@pytest.mark.asyncio
async def test_execute_missing_task_id(mock_tools):
    """Test execution without task_id."""
    result = await execute_tools("", "[]", mock_tools)

    assert result.failure
    assert "task_id required" in result.error


@pytest.mark.asyncio
async def test_working_memory_records_actions(mock_tools):
    """Test that tool executions are recorded in working memory."""
    from unittest.mock import patch

    tools_json = '[{"name": "file_write", "args": {"filename": "test.txt", "content": "hello"}}]'

    with patch("cogency.core.execute.working") as mock_working:
        result = await execute_tools("task123", tools_json, mock_tools)

        assert result.success
        mock_working.actions.assert_called_once()
        call_args = mock_working.actions.call_args[0]
        assert call_args[0] == "task123"  # task_id
        assert call_args[1]["tool"] == "file_write"
        assert call_args[1]["args"] == {"filename": "test.txt", "content": "hello"}
        assert call_args[1]["result"] == "File written successfully"


@pytest.mark.asyncio
async def test_execute_tool_failures_graceful():
    """Test graceful handling of multiple tool failures."""
    # Mock tools with different failure modes
    failing_tools = {
        "timeout_tool": AsyncMock(name="timeout_tool"),
        "error_tool": AsyncMock(name="error_tool"),
        "missing_tool": None,  # Tool doesn't exist
    }

    failing_tools["timeout_tool"].execute.return_value = Err("Tool timeout")
    failing_tools["error_tool"].execute.return_value = Err("Internal error")

    # Test individual failures handle gracefully
    timeout_result = await execute_tools(
        "task1", '[{"name": "timeout_tool", "args": {}}]', failing_tools
    )
    assert timeout_result.failure
    assert "timeout" in timeout_result.error.lower()

    error_result = await execute_tools(
        "task2", '[{"name": "error_tool", "args": {}}]', failing_tools
    )
    assert error_result.failure
    assert "error" in error_result.error.lower()


@pytest.mark.asyncio
async def test_execute_invalid_tool_args(mock_tools):
    """Test handling of invalid tool argument types."""
    # Test various invalid argument scenarios
    test_cases = [
        ('{"name": "file_write"}', "missing args field"),  # Missing args
        ('[{"name": "file_write", "args": "not_a_dict"}]', "args must be object"),  # String args
        ('[{"name": 123, "args": {}}]', "tool name must be string"),  # Numeric name
    ]

    for tools_json, _expected_error_type in test_cases:
        result = await execute_tools("task123", tools_json, mock_tools)
        assert result.failure  # Should handle gracefully, not crash
        # Should have some error message (specific content may vary)
        assert len(result.error) > 0
