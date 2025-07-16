import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

from cogency.nodes.react_loop import _complexity_score, reason_phase, act_phase, respond_phase, _fallback_response, REASON_PROMPT, RESPONSE_PROMPT
from cogency.common.types import AgentState, ReasoningDecision, Context
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.common.schemas import ToolCall, MultiToolCall

class TestReactLoopNode:

    @pytest.fixture
    def mock_agent_state(self):
        return AgentState(query="test query", response="", intermediate_steps=[], context=Context(current_input="test query"))

    @pytest.fixture
    def mock_llm(self):
        return AsyncMock(spec=BaseLLM)

    @pytest.fixture
    def mock_tool(self):
        mock = Mock(spec=BaseTool)
        mock.name = "test_tool"
        mock.description = "A test tool"
        mock.get_schema.return_value = "test_schema"
        return mock

    @pytest.fixture
    def mock_tools(self, mock_tool):
        return [mock_tool]

    # Test _complexity_score
    def test_complexity_score(self):
        assert _complexity_score("simple query", 0) == pytest.approx(0.1)
        assert _complexity_score("long query " * 50, 0) > 0.1
        assert _complexity_score("analyze this", 0) > 0.1
        assert _complexity_score("analyze this", 10) > _complexity_score("analyze this", 0)
        assert _complexity_score("very long query with analyze and compare and evaluate and research", 15) == pytest.approx(1.0)

    # Test reason_phase
    @pytest.mark.asyncio
    async def test_reason_phase_respond_directly(self, mock_agent_state, mock_llm, mock_tools):
        mock_llm.invoke.return_value = json.dumps({"action": "respond", "answer": "direct answer"})
        
        with patch("cogency.react.response_parser.ReactResponseParser") as MockParser:
            mock_parser_instance = MockParser.return_value
            mock_parser_instance.can_answer_directly.return_value = True
            mock_parser_instance.extract_answer.return_value = "direct answer"
            mock_parser_instance.extract_tool_calls.return_value = None

            result = await reason_phase(mock_agent_state, mock_llm, mock_tools)

            mock_llm.invoke.assert_called_once()
            assert result["can_answer_directly"] is True
            assert result["direct_response"] == "direct answer"
            assert result["tool_calls"] is None
            assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
            assert mock_agent_state["context"].messages[-1]["content"] == json.dumps({"action": "respond", "answer": "direct answer"})

    @pytest.mark.asyncio
    async def test_reason_phase_use_single_tool(self, mock_agent_state, mock_llm, mock_tools):
        tool_call_str = json.dumps({"action": "use_tool", "tool_call": {"name": "test_tool", "args": {"param": "value"}}})
        mock_llm.invoke.return_value = tool_call_str

        with patch("cogency.react.response_parser.ReactResponseParser") as MockParser:
            mock_parser_instance = MockParser.return_value
            mock_parser_instance.can_answer_directly.return_value = False
            mock_parser_instance.extract_answer.return_value = None
            mock_parser_instance.extract_tool_calls.return_value = tool_call_str

            result = await reason_phase(mock_agent_state, mock_llm, mock_tools)

            mock_llm.invoke.assert_called_once()
            assert result["can_answer_directly"] is False
            assert result["direct_response"] is None
            assert result["tool_calls"] == tool_call_str
            assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
            assert mock_agent_state["context"].messages[-1]["content"] == tool_call_str

    @pytest.mark.asyncio
    async def test_reason_phase_use_multi_tool(self, mock_agent_state, mock_llm, mock_tools):
        multi_tool_call_str = json.dumps({"action": "use_tools", "tool_call": {"calls": [{"name": "test_tool", "args": {"param": "value"}}, {"name": "another_tool", "args": {"param2": "value2"}}]}})
        mock_llm.invoke.return_value = multi_tool_call_str

        with patch("cogency.react.response_parser.ReactResponseParser") as MockParser:
            mock_parser_instance = MockParser.return_value
            mock_parser_instance.can_answer_directly.return_value = False
            mock_parser_instance.extract_answer.return_value = None
            mock_parser_instance.extract_tool_calls.return_value = multi_tool_call_str

            result = await reason_phase(mock_agent_state, mock_llm, mock_tools)

            mock_llm.invoke.assert_called_once()
            assert result["can_answer_directly"] is False
            assert result["direct_response"] is None
            assert result["tool_calls"] == multi_tool_call_str
            assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
            assert mock_agent_state["context"].messages[-1]["content"] == multi_tool_call_str

    # Test act_phase
    @pytest.mark.asyncio
    async def test_act_phase_no_tool_calls(self, mock_agent_state, mock_tools):
        reasoning = {"tool_calls": None}
        result = await act_phase(reasoning, mock_agent_state, mock_tools)
        assert result["type"] == "no_action"
        assert "time" in result

    @pytest.mark.asyncio
    async def test_act_phase_single_tool_success(self, mock_agent_state, mock_tools):
        tool_call_str = json.dumps({"action": "use_tool", "tool_call": {"name": "test_tool", "args": {"param": "value"}}})
        reasoning = {"tool_calls": tool_call_str}
        
        with patch("cogency.nodes.react_loop.execute_single_tool", new_callable=AsyncMock) as mock_execute_single_tool:
            mock_execute_single_tool.return_value = ("test_tool", {"param": "value"}, {"result": "tool output"})
            result = await act_phase(reasoning, mock_agent_state, mock_tools)

            mock_execute_single_tool.assert_called_once_with("test_tool", {"param": "value"}, mock_tools)
            assert result["type"] == "tool_execution"
            assert result["results"]["success"] is True
            assert "tool output" in mock_agent_state["context"].messages[-1]["content"]
            assert mock_agent_state["context"].tool_results[-1].tool_name == "test_tool"

    @pytest.mark.asyncio
    async def test_act_phase_single_tool_failure(self, mock_agent_state, mock_tools):
        tool_call_str = json.dumps({"action": "use_tool", "tool_call": {"name": "test_tool", "args": {"param": "value"}}})
        reasoning = {"tool_calls": tool_call_str}
        
        with patch("cogency.nodes.react_loop.execute_single_tool", new_callable=AsyncMock) as mock_execute_single_tool:
            mock_execute_single_tool.return_value = ("test_tool", {"param": "value"}, {"success": False, "error": "tool error"})
            result = await act_phase(reasoning, mock_agent_state, mock_tools)

            mock_execute_single_tool.assert_called_once_with("test_tool", {"param": "value"}, mock_tools)
            assert result["type"] == "tool_execution"
            assert result["results"]["success"] is False
            assert "Tool test_tool failed: tool error" in mock_agent_state["context"].messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_act_phase_multi_tool_success(self, mock_agent_state, mock_tools):
        multi_tool_call_str = json.dumps({"action": "use_tools", "tool_call": {"calls": [{"name": "test_tool", "args": {"param": "value"}}]}})
        reasoning = {"tool_calls": multi_tool_call_str}
        
        with patch("cogency.nodes.react_loop.execute_parallel_tools", new_callable=AsyncMock) as mock_execute_parallel_tools:
            mock_execute_parallel_tools.return_value = {"success": True, "results": ["output1", "output2"]}
            result = await act_phase(reasoning, mock_agent_state, mock_tools)

            mock_execute_parallel_tools.assert_called_once()
            assert result["type"] == "tool_execution"
            assert result["results"]["success"] is True

    # Test respond_phase
    @pytest.mark.asyncio
    async def test_respond_phase_success(self, mock_agent_state, mock_llm):
        action = {"results": {"success": True}}
        mock_llm.invoke.return_value = "Final response"

        result = await respond_phase(action, mock_agent_state, mock_llm)

        mock_llm.invoke.assert_called_once()
        assert result["text"] == "Final response"
        assert result["decision"].should_respond is True
        assert result["decision"].task_complete is True
        assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
        assert mock_agent_state["context"].messages[-1]["content"] == "Final response"

    @pytest.mark.asyncio
    async def test_respond_phase_failure(self, mock_agent_state, mock_llm):
        action = {"results": {"success": False}}
        mock_llm.invoke.return_value = "Error response"

        result = await respond_phase(action, mock_agent_state, mock_llm)

        mock_llm.invoke.assert_called_once()
        assert result["text"] == "Error response"
        assert result["decision"].should_respond is True
        assert result["decision"].task_complete is True
        assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
        assert mock_agent_state["context"].messages[-1]["content"] == "Error response"

    # Test _fallback_response
    @pytest.mark.asyncio
    async def test_fallback_response(self, mock_agent_state, mock_llm):
        mock_llm.invoke.return_value = "Fallback summary"
        
        with patch("cogency.nodes.react_loop.apply_response_shaping", new_callable=AsyncMock) as mock_apply_response_shaping:
            mock_apply_response_shaping.return_value = "Shaped fallback summary"
            result = await _fallback_response(mock_agent_state, mock_llm, "max_iterations", response_shaper={"profile": "conversational"})

            mock_llm.invoke.assert_called_once()
            mock_apply_response_shaping.assert_called_once_with("Fallback summary", mock_llm, {"profile": "conversational"})
            assert result["text"] == "Shaped fallback summary"
            assert result["decision"].should_respond is True
            assert result["decision"].task_complete is True
            assert "assistant" in mock_agent_state["context"].messages[-1]["role"]
            assert mock_agent_state["context"].messages[-1]["content"] == "Fallback summary"
