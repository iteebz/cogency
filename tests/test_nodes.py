import json
from unittest.mock import AsyncMock

import pytest

from cogency.context import Context
from cogency.nodes.act import act
from cogency.nodes.plan import plan
from cogency.nodes.reason import reason
from cogency.nodes.reflect import reflect
from cogency.nodes.respond import respond
from cogency.tools.calculator import CalculatorTool


class TestPlanNode:
    """Test suite for plan node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = AsyncMock()
        self.calculator = CalculatorTool()
        self.context = Context(current_input="What is 2 + 2?")
        self.state = {"context": self.context, "execution_trace": None}

    import pytest

    @pytest.mark.asyncio
    async def test_plan_with_tools_direct_response(self):
        """Test plan node with tools when direct response is needed."""
        response_payload = {"action": "direct_response", "answer": "Hello"}
        self.mock_llm.invoke.return_value = f"{response_payload}"

        result = await plan(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert result["context"].messages[0]["content"] == f"{response_payload}"
        self.mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_with_tools_tool_needed(self):
        """Test plan node when tool is needed."""
        response_payload = {"action": "tool_needed", "reasoning": "need calc"}
        self.mock_llm.invoke.return_value = f"{response_payload}"

        result = await plan(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert result["context"].messages[0]["content"] == f"{response_payload}"

    @pytest.mark.asyncio
    async def test_plan_without_tools(self):
        """Test plan node without tools."""
        response_payload = {
            "action": "direct_response",
            "answer": "No tools available",
        }
        self.mock_llm.invoke.return_value = f"{response_payload}"

        await plan(self.state, self.mock_llm, [])

        # Check that system prompt mentions "no tools"
        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]
        assert "no tools" in system_message["content"]

    @pytest.mark.asyncio
    async def test_plan_prompt_format(self):
        """Test that plan prompt is properly formatted."""
        response_payload = {"action": "direct_response", "answer": "test"}
        self.mock_llm.invoke.return_value = f"{response_payload}"

        await plan(self.state, self.mock_llm, [self.calculator])

        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]
        user_message = call_args[1]

        assert system_message["role"] == "system"
        assert "calculator" in system_message["content"]
        assert user_message["role"] == "user"
        assert user_message["content"] == "What is 2 + 2?"


class TestReasonNode:
    """Test suite for reason node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = AsyncMock()
        self.calculator = CalculatorTool()
        self.context = Context(current_input="Calculate 2 + 2")
        self.state = {"context": self.context, "execution_trace": None}

    @pytest.mark.asyncio
    async def test_reason_with_tools(self):
        """Test reason node with tools."""
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        self.mock_llm.invoke.return_value = tool_call

        result = await reason(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert result["context"].messages[0]["content"] == tool_call

    @pytest.mark.asyncio
    async def test_reason_without_tools(self):
        """Test reason node without tools."""
        self.mock_llm.invoke.return_value = "I cannot perform calculations without tools."

        await reason(self.state, self.mock_llm, [])

        # Check that no tool instructions are added when no tools available
        call_args = self.mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1  # Only user message
        assert call_args[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_reason_with_list_response(self):
        """Test reason node when LLM returns a list."""
        self.mock_llm.invoke.return_value = ["I", "need", "calculator"]

        result = await reason(self.state, self.mock_llm, [self.calculator])

        assert result["context"].messages[0]["content"] == "I need calculator"

    @pytest.mark.asyncio
    async def test_reason_prompt_includes_schemas(self):
        """Test that reason prompt includes tool schemas."""
        tool_call = "TOOL_CALL: calculator(operation='add', x1=1, x2=2)"
        self.mock_llm.invoke.return_value = tool_call

        await reason(self.state, self.mock_llm, [self.calculator])

        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]

        assert system_message["role"] == "system"
        assert "calculator" in system_message["content"]
        assert "Schema:" in system_message["content"]


class TestActNode:
    """Test suite for act node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = CalculatorTool()
        self.context = Context(current_input="Calculate 2 + 2")
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        self.context.add_message("assistant", tool_call)
        self.state = {"context": self.context, "execution_trace": None}

    @pytest.mark.asyncio
    async def test_act_successful_tool_call(self):
        """Test act node with successful tool execution."""
        result = await act(self.state, [self.calculator])

        assert result["context"] == self.context
        # Should have original message + system message with result
        assert len(result["context"].messages) == 2
        assert result["context"].messages[1]["role"] == "system"
        assert "4" in result["context"].messages[1]["content"]

    @pytest.mark.asyncio
    async def test_act_tool_not_found(self):
        """Test act node when tool is not found."""
        self.context.messages[-1]["content"] = "TOOL_CALL: unknown_tool(arg=value)"

        result = await act(self.state, [self.calculator])

        # Should add error message
        assert len(result["context"].messages) == 2
        assert "not found" in result["context"].messages[1]["content"]

    @pytest.mark.asyncio
    async def test_act_no_tool_call(self):
        """Test act node when no tool call is present."""
        self.context.messages[-1]["content"] = "Just a regular message"

        result = await act(self.state, [self.calculator])

        # Should not add any new messages
        assert len(result["context"].messages) == 1

    @pytest.mark.asyncio
    async def test_act_argument_parsing(self):
        """Test act node argument parsing logic."""
        # Test different argument types
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2.5, x2=3)"
        self.context.messages[-1]["content"] = tool_call

        result = await act(self.state, [self.calculator])

        # Should successfully parse float and int
        assert len(result["context"].messages) == 2
        assert "5.5" in result["context"].messages[1]["content"]

    @pytest.mark.asyncio
    async def test_act_string_arguments(self):
        """Test act node with string arguments."""
        # Mock a tool that accepts strings
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.validate_and_run = AsyncMock(return_value={"result": "success"})

        tool_call = "TOOL_CALL: test_tool(text='hello world')"
        self.context.messages[-1]["content"] = tool_call

        await act(self.state, [mock_tool])

        mock_tool.validate_and_run.assert_called_once_with(text="hello world")


class TestReflectNode:
    """Test suite for reflect node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = AsyncMock()
        self.context = Context(current_input="What is 2 + 2?")
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        self.context.add_message("assistant", tool_call)
        self.context.add_message("system", "4")
        self.state = {"context": self.context, "execution_trace": None}

    @pytest.mark.asyncio
    async def test_reflect_continue_status(self):
        """Test reflect node returning continue status."""
        response_payload = {"status": "continue", "assessment": "Need more info"}
        self.mock_llm.invoke.return_value = f"{response_payload}"

        result = await reflect(self.state, self.mock_llm)

        assert result["context"] == self.context
        assert len(result["context"].messages) == 3
        assert "continue" in result["context"].messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_reflect_complete_status(self):
        """Test reflect node returning complete status."""
        response_payload = {"status": "complete", "assessment": "Task done"}
        self.mock_llm.invoke.return_value = f"{response_payload}"

        result = await reflect(self.state, self.mock_llm)

        assert "complete" in result["context"].messages[-1]["content"]


class TestRespondNode:
    """Test suite for respond node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = AsyncMock()
        self.context = Context(current_input="What is 2 + 2?")
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        self.context.add_message("assistant", tool_call)
        self.context.add_message("system", "4")
        self.state = {"context": self.context, "execution_trace": None}

    @pytest.mark.asyncio
    async def test_respond_generates_final_response(self):
        """Test respond node generates final response."""
        # Change the system message to a non-JSON string to avoid parsing issues
        self.context.messages[-1]["content"] = "Calculator result: 4"
        self.mock_llm.invoke.return_value = "The answer is 4."

        result = await respond(self.state, self.mock_llm)

        assert result["context"] == self.context
        assert len(result["context"].messages) == 2
        assert result["context"].messages[-1]["content"] == "The answer is 4."
        assert result["context"].messages[-1]["role"] == "system"

    @pytest.mark.asyncio
    async def test_respond_with_direct_response_json(self):
        """Test respond node with direct response JSON."""
        response_payload = {
            "action": "direct_response",
            "answer": "The answer is 4",
        }
        self.context.messages[-1]["content"] = json.dumps(response_payload)

        result = await respond(self.state, self.mock_llm)

        # Should replace JSON with clean answer, no LLM call
        assert result["context"].messages[-1]["content"] == "The answer is 4"
        self.mock_llm.invoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_respond_with_invalid_json(self):
        """Test respond node with invalid JSON."""
        self.context.messages[-1]["content"] = '{"invalid": json}'
        self.mock_llm.invoke.return_value = "I cannot parse that response."

        result = await respond(self.state, self.mock_llm)

        # Should call LLM and replace message
        assert result["context"].messages[-1]["content"] == "I cannot parse that response."
        self.mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_with_conversation_history(self):
        """Test respond node uses conversation history."""
        # Change the system message to a non-JSON string to avoid parsing issues
        self.context.messages[-1]["content"] = "Calculator result: 4"
        self.mock_llm.invoke.return_value = "Based on the calculation, the answer is 4."

        await respond(self.state, self.mock_llm)

        # Check that LLM was called with full conversation history plus system prompt
        call_args = self.mock_llm.invoke.call_args[0][0]
        assert len(call_args) >= 3  # System prompt + previous messages
        assert call_args[0]["role"] == "system"  # First should be system prompt
