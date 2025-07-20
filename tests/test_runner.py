"""Test runner execution."""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from cogency.runner import StreamingRunner, WorkflowRunner
from cogency.types import AgentState


class TestWorkflowRunner:
    """Test basic workflow execution."""
    
    @pytest.mark.asyncio
    async def test_basic_execution(self, agent_state):
        """Basic execution should work without errors."""
        runner = WorkflowRunner()
        
        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})
        
        result = await runner.execute(mock_workflow, agent_state)
        
        assert result["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_execution_with_callback(self, agent_state):
        """Execution with streaming callback should work."""
        runner = WorkflowRunner()
        
        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})
        
        # Mock callback
        callback = AsyncMock()
        
        result = await runner.execute(mock_workflow, agent_state, callback)
        
        assert result["result"] == "success"


class TestStreamingRunner:
    """Test streaming execution behavior."""
    
    @pytest.mark.asyncio
    async def test_streaming_execution(self, agent_state):
        """Streaming execution should work."""
        runner = StreamingRunner()
        
        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})
        
        # Mock callback
        callback = AsyncMock()
        
        result = await runner.stream_execute(mock_workflow, agent_state, callback)
        
        assert result["result"] == "success"