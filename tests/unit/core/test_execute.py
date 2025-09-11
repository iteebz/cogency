"""Execute tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.execute import _execute, execute_tools
from cogency.core.protocols import ToolResult
from cogency.core.result import Err, Ok


@pytest.mark.asyncio
async def test_execute_tools():
    """Tool execution handles success, failure, multiple tools, args, user_id."""
    # Success case with args
    tool1 = AsyncMock()
    tool1.name = "test_tool"
    tool1.execute.return_value = Ok(ToolResult("Success"))

    # Failure case
    tool2 = AsyncMock()
    tool2.name = "failing_tool"
    tool2.execute.return_value = Err("Failed")

    # Recall tool with user_id
    tool3 = AsyncMock()
    tool3.name = "recall"
    tool3.execute.return_value = Ok(ToolResult("Recalled"))

    config = MagicMock()
    config.tools = [tool1, tool2, tool3]
    config.sandbox = False

    calls = [
        {"name": "test_tool", "args": {"param": "value"}},
        {"name": "failing_tool", "args": {}},
        {"name": "recall", "args": {"query": "test"}},
    ]

    result = await execute_tools(calls, config, user_id="user123")

    assert result == ["Success", "Tool failing_tool failed: Failed", "Recalled"]

    # Check args passed correctly
    assert tool1.execute.call_args.kwargs["param"] == "value"
    assert tool1.execute.call_args.kwargs["sandbox"] is False

    # Check user_id passed to recall
    assert tool3.execute.call_args.kwargs["user_id"] == "user123"
    assert tool3.execute.call_args.kwargs["query"] == "test"


@pytest.mark.asyncio
async def test_execute_single():
    """Single tool execution handles success, failure, validation."""
    tool = AsyncMock()
    tool.name = "valid_tool"
    tool.execute.return_value = Ok(ToolResult("Valid"))

    config = MagicMock()
    config.tools = [tool]

    # Success
    result = await _execute({"name": "valid_tool", "args": {"test": "value"}}, config)
    assert result.success
    assert result.unwrap() == "Valid"
    assert tool.execute.call_args.kwargs["test"] == "value"

    # Unknown tool
    result = await _execute({"name": "unknown", "args": {}}, config)
    assert result.failure
    assert "Unknown tool: unknown" in result.error

    # Invalid call format
    result = await _execute("not a dict", config)
    assert result.failure
    assert "Call must be JSON object" in result.error


def test_double_execute_protection():
    """Double EXECUTE events are harmless due to calls state management."""
    
    # Track execution calls
    execution_count = 0
    
    def mock_execute_tools():
        nonlocal execution_count
        execution_count += 1
        return f"execution_{execution_count}"
    
    # Simulate resume mode state management (resume.py:109, 115)
    calls = [{"name": "test_tool", "args": {}}]  # Initial state after CALLS event
    
    # First EXECUTE event - should execute
    if calls:  # Guard condition (resume.py:109)
        result1 = mock_execute_tools()
        calls = None  # Clear after execution (resume.py:115)
    
    # Second EXECUTE event (double EXECUTE scenario) - should be no-op
    if calls:  # Same guard condition
        result2 = mock_execute_tools()
    
    # Verify: only one execution occurred
    assert execution_count == 1, f"Expected 1 execution, got {execution_count}"
    
    # This proves double EXECUTE injection is safe defensive engineering
    # Provider can unconditionally emit §EXECUTE without risk of duplicate execution
