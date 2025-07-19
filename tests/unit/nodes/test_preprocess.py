"""Tests for preprocess node - routing, memory extraction, tool filtering."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.nodes.preprocess import preprocess_node
from cogency.common.types import AgentState
from cogency.context import Context


class TestPreprocessNode:
    """Test preprocess node functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM."""
        llm = AsyncMock()
        llm.invoke = AsyncMock(return_value="Mock response")
        return llm

    @pytest.fixture  
    def mock_tools(self):
        """Mock tools list."""
        tools = []
        for i in range(3):
            tool = Mock()
            tool.name = f"tool_{i}"
            tool.description = f"Tool {i} description"
            tools.append(tool)
        return tools

    @pytest.fixture
    def mock_memory(self):
        """Mock memory backend."""
        return AsyncMock()

    @pytest.fixture
    def sample_state(self):
        """Sample agent state."""
        context = Context(user_id="test_user")
        context.current_input = "Test query"
        return {
            "query": "Test query",
            "context": context
        }

    @pytest.mark.asyncio
    async def test_preprocess_simple_query(self, sample_state, mock_llm, mock_tools, mock_memory):
        """Test preprocessing simple query that should bypass ReAct."""
        sample_state["query"] = "Hello"
        
        result = await preprocess_node(
            sample_state,
            llm=mock_llm,
            tools=mock_tools,
            memory=mock_memory
        )
        
        assert result["next_node"] == "respond"
        assert result["direct_response_bypass"] is True
        assert "selected_tools" in result
        assert "adaptive_controller" in result

    @pytest.mark.asyncio  
    async def test_preprocess_complex_query(self, sample_state, mock_llm, mock_tools, mock_memory):
        """Test preprocessing complex query that needs ReAct."""
        sample_state["query"] = "Search for weather data and calculate statistics"
        
        result = await preprocess_node(
            sample_state,
            llm=mock_llm,
            tools=mock_tools,
            memory=mock_memory
        )
        
        assert result["next_node"] == "reason"
        assert result["direct_response_bypass"] is False
        assert "selected_tools" in result
        assert "adaptive_controller" in result
        assert "complexity_score" in result