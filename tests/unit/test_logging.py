"""Test retrospective logs access via agent.logs()."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency import Agent
from tests.fixtures.llm import MockLLM


@pytest.mark.asyncio
async def test_logs_after_execution():
    """Test that logs are available retrospectively after agent execution."""
    # Mock executor with logs method
    mock_executor = Mock()
    mock_executor.run = AsyncMock(return_value="Test response")

    # Create expected logs structure
    import time

    timestamp = time.time()

    expected_logs = [
        {"timestamp": timestamp, "type": "triage", "state": "planning"},
        {"timestamp": timestamp, "type": "reason", "state": "thinking"},
        {"timestamp": timestamp, "type": "tool", "name": "shell", "ok": True, "result": "output"},
        {"timestamp": timestamp, "type": "respond", "state": "complete"},
    ]

    mock_executor.logs = Mock(return_value=expected_logs)

    # Create agent and set executor
    agent = Agent("test", llm=MockLLM(), tools=[])
    agent._executor = mock_executor

    # Execute agent
    result = await agent.run_async("test query")
    assert result == "Test response"

    # Get logs retrospectively
    logs = agent.logs()

    # Verify logs structure
    assert len(logs) == 4
    assert logs[0]["type"] == "triage"
    assert logs[0]["state"] == "planning"
    assert "timestamp" in logs[0]

    assert logs[1]["type"] == "reason"
    assert logs[1]["state"] == "thinking"

    assert logs[2]["type"] == "tool"
    assert logs[2]["name"] == "shell"
    assert logs[2]["ok"] is True
    assert logs[2]["result"] == "output"

    assert logs[3]["type"] == "respond"
    assert logs[3]["state"] == "complete"


@pytest.mark.asyncio
async def test_logs_work_without_debug():
    """Test that logs work regardless of debug setting."""
    # Mock executor with debug=False
    mock_executor = Mock()
    mock_executor.debug = False  # Explicitly set debug to False

    import time

    expected_logs = [{"timestamp": time.time(), "type": "test", "message": "debug disabled"}]

    mock_executor.logs = Mock(return_value=expected_logs)

    agent = Agent("test", llm=MockLLM(), tools=[])
    agent._executor = mock_executor

    # Logs should still work
    logs = agent.logs()
    assert len(logs) == 1
    assert logs[0]["type"] == "test"
    assert logs[0]["message"] == "debug disabled"


def test_logs_empty_before_execution():
    """Test that logs return empty list before execution."""
    agent = Agent("test", llm=MockLLM(), tools=[])
    logs = agent.logs()
    assert logs == []


@pytest.mark.asyncio
async def test_logs_multiple_executions():
    """Test that logs accumulate across multiple executions."""
    mock_executor = Mock()
    mock_executor.run = AsyncMock(return_value="Response")

    agent = Agent("test", llm=MockLLM(), tools=[])
    agent._executor = mock_executor

    import time

    # First execution
    await agent.run_async("query 1")
    # Mock logs after first execution
    mock_executor.logs = Mock(
        return_value=[{"timestamp": time.time(), "type": "first", "query": "query 1"}]
    )

    # Second execution
    await agent.run_async("query 2")
    # Mock logs after second execution - should accumulate
    mock_executor.logs = Mock(
        return_value=[
            {"timestamp": time.time(), "type": "first", "query": "query 1"},
            {"timestamp": time.time(), "type": "second", "query": "query 2"},
        ]
    )

    # Logs should contain both
    logs = agent.logs()
    assert len(logs) == 2
    assert logs[0]["type"] == "first"
    assert logs[0]["query"] == "query 1"
    assert logs[1]["type"] == "second"
    assert logs[1]["query"] == "query 2"
