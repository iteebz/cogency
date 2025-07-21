"""Test runner execution."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.runner import FlowRunner, StreamRunner


class TestFlowRunner:
    """Test basic workflow execution."""

    @pytest.mark.asyncio
    async def test_basic_execution(self, agent_state):
        """Basic execution should work without errors."""
        runner = FlowRunner()

        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})

        result = await runner.execute(mock_workflow, agent_state)

        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_execution_with_callback(self, agent_state):
        """Execution with streaming callback should work."""
        runner = FlowRunner()

        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})

        # Mock callback
        callback = AsyncMock()

        result = await runner.execute(mock_workflow, agent_state, callback)

        assert result["result"] == "success"


class TestStreamRunner:
    """Test streaming execution behavior."""

    @pytest.mark.asyncio
    async def test_streaming_execution(self, agent_state):
        """Streaming execution should work."""
        runner = StreamRunner()

        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})

        # Mock callback
        callback = AsyncMock()

        result = await runner.stream(mock_workflow, agent_state, callback)

        assert result["result"] == "success"
