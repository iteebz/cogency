import pytest
from unittest.mock import AsyncMock, Mock
from cogency.nodes.select_tools import select_tools
from cogency.context import Context
from cogency.types import AgentState, ExecutionTrace
from cogency.tools.base import BaseTool


@pytest.fixture
def mock_llm():
    mock = AsyncMock()
    mock.invoke.return_value = '{"relevant_tools": ["tool1"]}'  # Default mock response
    return mock

@pytest.fixture
def mock_tools():
    tool1 = Mock(spec=BaseTool)
    tool1.name = "tool1"
    tool1.description = "Description for tool1"
    tool2 = Mock(spec=BaseTool)
    tool2.name = "tool2"
    tool2.description = "Description for tool2"
    tool3 = Mock(spec=BaseTool)
    tool3.name = "tool3"
    tool3.description = "Description for tool3"
    tool4 = Mock(spec=BaseTool)
    tool4.name = "tool4"
    tool4.description = "Description for tool4"
    return [tool1, tool2, tool3, tool4]

@pytest.fixture
def agent_state():
    context = Context(current_input="test query")
    return AgentState(context=context, trace=ExecutionTrace(), query="test query")


class TestSelectToolsNode:
    """Test the select_tools node."""

    @pytest.mark.asyncio
    async def test_select_tools_few_tools_no_llm_call(self, mock_llm, agent_state, mock_tools):
        """Should not call LLM if there are 3 or fewer tools."""
        tools = mock_tools[:3]  # Use 3 tools
        
        result_state = await select_tools(agent_state, mock_llm, tools)
        
        mock_llm.invoke.assert_not_called()
        assert result_state["selected_tools"] == tools

    @pytest.mark.asyncio
    async def test_select_tools_many_tools_llm_call_success(self, mock_llm, agent_state, mock_tools):
        """Should call LLM and select tools based on its response."""
        mock_llm.invoke.return_value = '{"relevant_tools": ["tool1", "tool3"]}'
        
        result_state = await select_tools(agent_state, mock_llm, mock_tools)
        
        mock_llm.invoke.assert_called_once()
        selected_names = {tool.name for tool in result_state["selected_tools"]}
        assert selected_names == {"tool1", "tool3"}

    @pytest.mark.asyncio
    async def test_select_tools_llm_call_failure_fallback_all_tools(self, mock_llm, agent_state, mock_tools):
        """Should fallback to all tools if LLM call fails (e.g., malformed JSON)."""
        mock_llm.invoke.return_value = "this is not valid json"
        
        result_state = await select_tools(agent_state, mock_llm, mock_tools)
        
        mock_llm.invoke.assert_called_once()
        assert result_state["selected_tools"] == mock_tools

    @pytest.mark.asyncio
    async def test_select_tools_llm_returns_empty_list_fallback_all_tools(self, mock_llm, agent_state, mock_tools):
        """Should fallback to all tools if LLM returns an empty relevant_tools list."""
        mock_llm.invoke.return_value = '{"relevant_tools": []}'
        
        result_state = await select_tools(agent_state, mock_llm, mock_tools)
        
        mock_llm.invoke.assert_called_once()
        assert result_state["selected_tools"] == mock_tools

    @pytest.mark.asyncio
    async def test_select_tools_llm_returns_non_existent_tools(self, mock_llm, agent_state, mock_tools):
        """Should only select tools that actually exist."""
        mock_llm.invoke.return_value = '{"relevant_tools": ["tool1", "non_existent_tool"]}'
        
        result_state = await select_tools(agent_state, mock_llm, mock_tools)
        
        mock_llm.invoke.assert_called_once()
        selected_names = {tool.name for tool in result_state["selected_tools"]}
        assert selected_names == {"tool1"}
