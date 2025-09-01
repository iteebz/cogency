"""Execute tests - Tool execution pipeline coverage."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.execute import _execute, create_results_event, execute_tools
from cogency.core.protocols import Event, ToolResult
from cogency.core.result import Err, Ok


@pytest.mark.asyncio
async def test_execute_tools_basic():
    """Tool execution handles basic tool calls."""
    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"
    mock_tool.execute.return_value = Ok(ToolResult("Tool result"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = True

    calls = [{"name": "test_tool", "args": {}}]

    result = await execute_tools(calls, mock_config)

    assert result == ["Tool result"]
    assert mock_tool.execute.called


@pytest.mark.asyncio
async def test_execute_tools_multiple():
    """Tool execution handles multiple tool calls sequentially."""
    mock_tool1 = AsyncMock()
    mock_tool1.name = "tool1"
    mock_tool1.execute.return_value = Ok(ToolResult("Result 1"))
    mock_tool2 = AsyncMock()
    mock_tool2.name = "tool2"
    mock_tool2.execute.return_value = Ok(ToolResult("Result 2"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool1, mock_tool2]
    mock_config.sandbox = True

    calls = [{"name": "tool1", "args": {}}, {"name": "tool2", "args": {"param": "value"}}]

    result = await execute_tools(calls, mock_config)

    assert result == ["Result 1", "Result 2"]
    assert mock_tool1.execute.called
    assert mock_tool2.execute.called


@pytest.mark.asyncio
async def test_execute_tools_with_args():
    """Tool execution passes arguments correctly."""
    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"
    mock_tool.execute.return_value = Ok(ToolResult("Success"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = True

    calls = [{"name": "test_tool", "args": {"param": "value", "flag": True}}]

    result = await execute_tools(calls, mock_config)

    # Check that original args were passed (global context may be added)
    call_args = mock_tool.execute.call_args
    assert call_args.kwargs["param"] == "value"
    assert call_args.kwargs["flag"] is True
    assert result == ["Success"]


@pytest.mark.asyncio
async def test_execute_tools_user_id():
    """Tool execution passes user_id for recall tool."""
    mock_tool = AsyncMock()
    mock_tool.name = "recall"
    mock_tool.execute.return_value = Ok(ToolResult("Recall result"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = True

    calls = [{"name": "recall", "args": {"query": "test"}}]

    await execute_tools(calls, mock_config, user_id="test_user")

    # Check that recall got user_id and original args
    call_args = mock_tool.execute.call_args
    assert call_args.kwargs["query"] == "test"
    assert call_args.kwargs["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_execute_tools_failure():
    """Tool execution handles tool failures gracefully."""
    mock_tool = AsyncMock()
    mock_tool.name = "failing_tool"
    mock_tool.execute.return_value = Err("Tool failed")

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = True

    calls = [{"name": "failing_tool", "args": {}}]

    result = await execute_tools(calls, mock_config)

    assert result == ["Tool failing_tool failed: Tool failed"]


@pytest.mark.asyncio
async def test_execute_single_valid():
    """Single tool execution works correctly."""
    mock_tool = AsyncMock()
    mock_tool.name = "valid_tool"
    mock_tool.execute.return_value = Ok(ToolResult("Valid result"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = True

    call = {"name": "valid_tool", "args": {"test": "value"}}

    result = await _execute(call, mock_config)

    assert result.success
    assert result.unwrap() == "Valid result"
    # Check that original args were passed (global context may be added)
    call_args = mock_tool.execute.call_args
    assert call_args.kwargs["test"] == "value"


@pytest.mark.asyncio
async def test_execute_single_invalid_call():
    """Single tool execution rejects invalid call format."""
    mock_config = MagicMock()
    mock_config.tools = []

    result = await _execute("not a dict", mock_config)

    assert result.failure
    assert "Call must be JSON object" in result.error


@pytest.mark.asyncio
async def test_execute_single_unknown_tool():
    """Single tool execution handles unknown tools."""
    mock_config = MagicMock()
    mock_config.tools = []

    call = {"name": "unknown_tool", "args": {}}

    result = await _execute(call, mock_config)

    assert result.failure
    assert "Unknown tool: unknown_tool" in result.error


@pytest.mark.asyncio
async def test_execute_single_invalid_args():
    """Single tool execution rejects invalid args format."""
    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]

    call = {"name": "test_tool", "args": "not a dict"}

    result = await _execute(call, mock_config)

    assert result.failure
    assert "Tool 'args' must be JSON object" in result.error


@pytest.mark.asyncio
async def test_execute_single_exception():
    """Single tool execution handles tool exceptions."""
    mock_tool = AsyncMock()
    mock_tool.name = "exception_tool"
    mock_tool.execute.side_effect = Exception("Unexpected error")

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]

    call = {"name": "exception_tool", "args": {}}

    result = await _execute(call, mock_config)

    assert result.failure
    assert "execution failed: Unexpected error" in result.error


@pytest.mark.asyncio
async def test_execute_sandbox_flag():
    """Sandbox flag is passed to sandboxed tools."""
    mock_tool = AsyncMock()
    mock_tool.name = "read"
    mock_tool.execute.return_value = Ok(ToolResult("File content"))

    mock_config = MagicMock()
    mock_config.tools = [mock_tool]
    mock_config.sandbox = False

    call = {"name": "read", "args": {"filename": "test.txt"}}

    result = await _execute(call, mock_config)

    assert result.success
    mock_tool.execute.assert_called_with(filename="test.txt", sandbox=False)


def test_create_results_event():
    """Results event creation - canonical event structure."""
    individual_results = ["result1", "result2", "error: failed"]

    event = create_results_event(individual_results)

    # Canonical event structure
    assert event["type"] == Event.RESULTS
    assert "content" in event
    assert "results" in event
    assert "timestamp" in event

    # Content is JSON serialized
    import json

    parsed_content = json.loads(event["content"])
    assert parsed_content == individual_results

    # Results field is original list
    assert event["results"] == individual_results

    # Timestamp is recent float
    import time

    assert isinstance(event["timestamp"], float)
    assert abs(event["timestamp"] - time.time()) < 1.0  # Within 1 second


def test_create_results_event_empty():
    """Results event handles empty results - edge case."""
    event = create_results_event([])

    assert event["type"] == Event.RESULTS
    assert event["content"] == "[]"
    assert event["results"] == []


def test_create_results_event_complex():
    """Results event handles complex data structures."""
    complex_results = [
        {"tool": "file_read", "result": "content", "status": "ok"},
        "simple string result",
        ["nested", "list", "result"],
    ]

    event = create_results_event(complex_results)

    # Should serialize complex structures
    import json

    parsed = json.loads(event["content"])
    assert parsed == complex_results
    assert event["results"] == complex_results
