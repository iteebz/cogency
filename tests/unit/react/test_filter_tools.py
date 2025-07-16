import pytest
from unittest.mock import AsyncMock, Mock
import json

from cogency.react.filter_tools_node import filter_tools_node_node
from cogency.common.types import AgentState
from cogency.tools.base import BaseTool

class TestSelectToolsNode:
    @pytest.fixture
    def mock_agent_state(self):
        return AgentState(query="test query", response="", intermediate_steps=[])

    @pytest.fixture
    def mock_llm(self):
        mock = AsyncMock()
        mock.invoke.return_value = json.dumps({"relevant_tools": ["tool_a", "tool_c"]})
        return mock

    @pytest.fixture
    def mock_tools(self):
        tool_a = Mock(spec=BaseTool)
        tool_a.name = "tool_a"
        tool_a.description = "Description A"
        tool_b = Mock(spec=BaseTool)
        tool_b.name = "tool_b"
        tool_b.description = "Description B"
        tool_c = Mock(spec=BaseTool)
        tool_c.name = "tool_c"
        tool_c.description = "Description C"
        tool_d = Mock(spec=BaseTool)
        tool_d.name = "tool_d"
        tool_d.description = "Description D"
        return [tool_a, tool_b, tool_c, tool_d]

    @pytest.mark.asyncio
    async def test_select_tools_few_tools(self, mock_agent_state):
        few_tools = [Mock(spec=BaseTool, name="tool_1"), Mock(spec=BaseTool, name="tool_2")]
        mock_llm = AsyncMock()

        result_state = await filter_tools_node(mock_agent_state, mock_llm, few_tools)

        mock_llm.invoke.assert_not_called()
        assert result_state["selected_tools"] == few_tools
        assert result_state == mock_agent_state

    @pytest.mark.asyncio
    async def test_select_tools_many_tools_success(self, mock_agent_state, mock_llm, mock_tools):
        result_state = await filter_tools_node(mock_agent_state, mock_llm, mock_tools)

        expected_prompt = (
            "Request: \"test query\"\n\nTools:\n" +
            "- tool_a: Description A\n" +
            "- tool_b: Description B\n" +
            "- tool_c: Description C\n" +
            "- tool_d: Description D\n\n" +
            "Return JSON with relevant tools only:\n{\"relevant_tools\": [\"tool1\", \"tool2\"]}"
        )
        mock_llm.invoke.assert_called_once_with([{"role": "user", "content": expected_prompt}])
        
        expected_selected_tools = [mock_tools[0], mock_tools[2]] # tool_a and tool_c
        assert result_state["selected_tools"] == expected_selected_tools
        assert result_state == mock_agent_state

    @pytest.mark.asyncio
    async def test_select_tools_llm_failure_fallback(self, mock_agent_state, mock_tools):
        mock_llm_fail = AsyncMock()
        mock_llm_fail.invoke.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

        result_state = await filter_tools_node(mock_agent_state, mock_llm_fail, mock_tools)

        mock_llm_fail.invoke.assert_called_once()
        assert result_state["selected_tools"] == mock_tools
        assert result_state == mock_agent_state

    @pytest.mark.asyncio
    async def test_select_tools_no_tools(self, mock_agent_state, mock_llm):
        result_state = await filter_tools_node(mock_agent_state, mock_llm, [])

        mock_llm.invoke.assert_not_called()
        assert result_state["selected_tools"] == []
        assert result_state == mock_agent_state
