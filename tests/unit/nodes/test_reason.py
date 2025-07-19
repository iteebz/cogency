"""Tests for reason node - pure reasoning and decision making."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.nodes.reason import reason_node
from cogency.common.types import AgentState, ReasoningDecision
from cogency.context import Context
from cogency.reasoning.adaptive import ReasonController, StoppingCriteria


class TestReasonNode:
    """Test reason node functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM."""
        llm = AsyncMock()
        llm.invoke = AsyncMock(return_value="I need to search for information")
        return llm

    @pytest.fixture  
    def mock_tools(self):
        """Mock tools list."""
        tools = []
        for i in range(3):
            tool = Mock()
            tool.name = f"tool_{i}"
            tool.get_schema = Mock(return_value=f"Schema for tool {i}")
            tools.append(tool)
        return tools

    @pytest.fixture
    def sample_state(self):
        """Sample agent state."""
        context = Context(user_id="test_user")
        context.current_input = "Test query"
        
        controller = ReasonController(StoppingCriteria())
        controller.start_reasoning()
        
        return {
            "query": "Test query",
            "context": context,
            "selected_tools": [],
            "adaptive_controller": controller
        }

    @pytest.mark.asyncio
    async def test_reason_generates_response(self, sample_state, mock_llm, mock_tools):
        """Test reason node generates reasoning response."""
        sample_state["selected_tools"] = mock_tools
        
        result = await reason_node(
            sample_state,
            llm=mock_llm,
            tools=mock_tools
        )
        
        assert "reasoning_decision" in result
        assert isinstance(result["reasoning_decision"], ReasoningDecision)
        assert result["next_node"] in ["respond", "act"]
        assert "last_node_output" in result

    @pytest.mark.asyncio
    async def test_reason_with_stopping_criteria(self, sample_state, mock_llm, mock_tools):
        """Test reason node respects stopping criteria."""
        # Set up controller to stop immediately
        controller = sample_state["adaptive_controller"]
        controller.metrics.iteration = 10  # Exceed max iterations
        
        result = await reason_node(
            sample_state,
            llm=mock_llm,
            tools=mock_tools
        )
        
        assert result["next_node"] == "respond"
        assert result["reasoning_decision"].task_complete is True