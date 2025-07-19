"""Tests for act node - pure tool execution."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.nodes.act import act_node
from cogency.common.types import AgentState
from cogency.context import Context


class TestActNode:
    """Test act node functionality."""

    @pytest.fixture  
    def mock_tools(self):
        """Mock tools list."""
        tools = []
        tool = Mock()
        tool.name = "search"
        tool.execute = AsyncMock(return_value={"result": "search results"})
        tools.append(tool)
        return tools

    @pytest.fixture
    def sample_state(self):
        """Sample agent state."""
        context = Context(user_id="test_user")
        context.current_input = "Test query"
        
        return {
            "query": "Test query", 
            "context": context,
            "tool_calls": "search('test query')"
        }

    @pytest.mark.asyncio
    async def test_act_executes_tool_call(self, sample_state, mock_tools):
        """Test act node executes tool calls."""
        result = await act_node(
            sample_state,
            tools=mock_tools
        )
        
        assert "execution_results" in result
        assert result["next_node"] == "reason"
        assert "execution_time" in result["execution_results"]

    @pytest.mark.asyncio
    async def test_act_no_tool_calls(self, sample_state, mock_tools):
        """Test act node with no tool calls."""
        sample_state["tool_calls"] = None
        
        result = await act_node(
            sample_state,
            tools=mock_tools
        )
        
        assert result["execution_results"]["type"] == "no_action"
        assert result["next_node"] == "reason"

    @pytest.mark.asyncio
    async def test_act_updates_controller_metrics(self, sample_state, mock_tools):
        """Test act node updates controller metrics."""
        from cogency.reasoning.adaptive import ReasonController, StoppingCriteria
        
        controller = ReasonController(StoppingCriteria())
        controller.start_reasoning()
        sample_state["adaptive_controller"] = controller
        
        result = await act_node(
            sample_state,
            tools=mock_tools
        )
        
        assert result["adaptive_controller"] == controller
        # Controller should have updated metrics after tool execution