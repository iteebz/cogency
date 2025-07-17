"""Pragmatic tests for filter_tools - core tool selection logic."""
import pytest
from unittest.mock import AsyncMock, Mock
import json

from cogency.react.filter_tools import filter_tools_node
from cogency.common.types import AgentState
from cogency.tools.base import BaseTool


class TestFilterToolsNode:
    """Test core tool filtering logic."""
    
    @pytest.fixture
    def mock_agent_state(self):
        return AgentState(query="test query", response="", intermediate_steps=[])

    @pytest.fixture
    def mock_tools(self):
        tool_a = Mock(spec=BaseTool)
        tool_a.name = "tool_a"
        tool_a.description = "Description A"
        tool_b = Mock(spec=BaseTool)
        tool_b.name = "tool_b"
        tool_b.description = "Description B"
        return [tool_a, tool_b]

    @pytest.mark.asyncio
    async def test_few_tools_bypass_llm(self, mock_agent_state):
        """Few tools should bypass LLM filtering."""
        few_tools = [Mock(spec=BaseTool, name="tool_1")]
        mock_llm = AsyncMock()

        result = await filter_tools_node(mock_agent_state, mock_llm, few_tools)

        mock_llm.invoke.assert_not_called()
        assert result["selected_tools"] == few_tools

    @pytest.mark.asyncio
    async def test_many_tools_use_llm(self, mock_agent_state, mock_tools):
        """Many tools should use LLM filtering."""
        # Add more tools to trigger LLM filtering
        tool_c = Mock(spec=BaseTool)
        tool_c.name = "tool_c"
        tool_c.description = "Description C"
        tool_d = Mock(spec=BaseTool)
        tool_d.name = "tool_d"
        tool_d.description = "Description D"
        many_tools = mock_tools + [tool_c, tool_d]
        
        mock_llm = AsyncMock()
        mock_llm.invoke.return_value = json.dumps({"relevant_tools": ["tool_a"]})

        result = await filter_tools_node(mock_agent_state, mock_llm, many_tools)

        mock_llm.invoke.assert_called_once()
        assert len(result["selected_tools"]) == 1
        assert result["selected_tools"][0].name == "tool_a"

    @pytest.mark.asyncio
    async def test_llm_failure_fallback(self, mock_agent_state, mock_tools):
        """LLM failure should fallback to all tools."""
        mock_llm = AsyncMock()
        mock_llm.invoke.side_effect = Exception("LLM failed")

        result = await filter_tools_node(mock_agent_state, mock_llm, mock_tools)

        assert result["selected_tools"] == mock_tools