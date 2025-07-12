from unittest.mock import Mock

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
        self.mock_llm = Mock()
        self.calculator = CalculatorTool()
        self.context = Context(current_input="What is 2 + 2?")
        self.state = {"context": self.context, "execution_trace": None}

    def test_plan_with_tools_direct_response(self):
        """Test plan node with tools when direct response is needed."""
        self.mock_llm.invoke.return_value = (
            '{"action": "direct_response", "answer": "Hello"}'
        )

        result = plan(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert (
            result["context"].messages[0]["content"]
            == '{"action": "direct_response", "answer": "Hello"}'
        )
        self.mock_llm.invoke.assert_called_once()

    def test_plan_with_tools_tool_needed(self):
        """Test plan node when tool is needed."""
        self.mock_llm.invoke.return_value = (
            '{"action": "tool_needed", "reasoning": "need calc"}'
        )

        result = plan(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert "tool_needed" in result["context"].messages[0]["content"]

    def test_plan_without_tools(self):
        """Test plan node without tools."""
        self.mock_llm.invoke.return_value = (
            '{"action": "direct_response", "answer": "No tools available"}'
        )

        plan(self.state, self.mock_llm, [])

        # Check that system prompt mentions "no tools"
        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]
        assert "no tools" in system_message["content"]

    def test_plan_prompt_format(self):
        """Test that plan prompt is properly formatted."""
        self.mock_llm.invoke.return_value = (
            '{"action": "direct_response", "answer": "test"}'
        )

        plan(self.state, self.mock_llm, [self.calculator])

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
        self.mock_llm = Mock()
        self.calculator = CalculatorTool()
        self.context = Context(current_input="Calculate 2 + 2")
        self.state = {"context": self.context, "execution_trace": None}

    def test_reason_with_tools(self):
        """Test reason node with tools."""
        self.mock_llm.invoke.return_value = (
            "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        )

        result = reason(self.state, self.mock_llm, [self.calculator])

        assert result["context"] == self.context
        assert len(result["context"].messages) == 1
        assert (
            "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
            in result["context"].messages[0]["content"]
        )

    def test_reason_without_tools(self):
        """Test reason node without tools."""
        self.mock_llm.invoke.return_value = (
            "I cannot perform calculations without tools."
        )

        reason(self.state, self.mock_llm, [])

        # Check that no tool instructions are added when no tools available
        call_args = self.mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1  # Only user message
        assert call_args[0]["role"] == "user"

    def test_reason_with_list_response(self):
        """Test reason node when LLM returns a list."""
        self.mock_llm.invoke.return_value = ["I", "need", "calculator"]

        result = reason(self.state, self.mock_llm, [self.calculator])

        assert result["context"].messages[0]["content"] == "I need calculator"

    def test_reason_prompt_includes_schemas(self):
        """Test that reason prompt includes tool schemas."""
        self.mock_llm.invoke.return_value = (
            "TOOL_CALL: calculator(operation='add', x1=1, x2=2)"
        )

        reason(self.state, self.mock_llm, [self.calculator])

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
        self.context.add_message(
            "assistant", "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        )
        self.state = {"context": self.context, "execution_trace": None}

    def test_act_successful_tool_call(self):
        """Test act node with successful tool execution."""
        result = act(self.state, [self.calculator])

        assert result["context"] == self.context
        # Should have original message + system message with result
        assert len(result["context"].messages) == 2
        assert result["context"].messages[1]["role"] == "system"
        assert "4" in result["context"].messages[1]["content"]

    def test_act_tool_not_found(self):
        """Test act node when tool is not found."""
        self.context.messages[-1]["content"] = "TOOL_CALL: unknown_tool(arg=value)"

        result = act(self.state, [self.calculator])

        # Should add error message
        assert len(result["context"].messages) == 2
        assert "not found" in result["context"].messages[1]["content"]

    def test_act_no_tool_call(self):
        """Test act node when no tool call is present."""
        self.context.messages[-1]["content"] = "Just a regular message"

        result = act(self.state, [self.calculator])

        # Should not add any new messages
        assert len(result["context"].messages) == 1

    def test_act_argument_parsing(self):
        """Test act node argument parsing logic."""
        # Test different argument types
        self.context.messages[-1][
            "content"
        ] = "TOOL_CALL: calculator(operation='add', x1=2.5, x2=3)"

        result = act(self.state, [self.calculator])

        # Should successfully parse float and int
        assert len(result["context"].messages) == 2
        assert "5.5" in result["context"].messages[1]["content"]

    def test_act_string_arguments(self):
        """Test act node with string arguments."""
        # Mock a tool that accepts strings
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.validate_and_run.return_value = {"result": "success"}

        self.context.messages[-1][
            "content"
        ] = "TOOL_CALL: test_tool(text='hello world')"

        act(self.state, [mock_tool])

        mock_tool.validate_and_run.assert_called_once_with(text="hello world")


class TestReflectNode:
    """Test suite for reflect node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = Mock()
        self.context = Context(current_input="What is 2 + 2?")
        self.context.add_message(
            "assistant", "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        )
        self.context.add_message("system", "4")
        self.state = {"context": self.context, "execution_trace": None}

    def test_reflect_continue_status(self):
        """Test reflect node returning continue status."""
        self.mock_llm.invoke.return_value = (
            '{"status": "continue", "assessment": "Need more info"}'
        )

        result = reflect(self.state, self.mock_llm)

        assert result["context"] == self.context
        assert len(result["context"].messages) == 3
        assert "continue" in result["context"].messages[-1]["content"]

    def test_reflect_complete_status(self):
        """Test reflect node returning complete status."""
        self.mock_llm.invoke.return_value = (
            '{"status": "complete", "assessment": "Task done"}'
        )

        result = reflect(self.state, self.mock_llm)

        assert "complete" in result["context"].messages[-1]["content"]


class TestRespondNode:
    """Test suite for respond node."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = Mock()
        self.context = Context(current_input="What is 2 + 2?")
        self.context.add_message(
            "assistant", "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        )
        self.context.add_message("system", "4")
        self.state = {"context": self.context, "execution_trace": None}

    def test_respond_generates_final_response(self):
        """Test respond node generates final response."""
        # Change the system message to a non-JSON string to avoid parsing issues
        self.context.messages[-1]["content"] = "Calculator result: 4"
        self.mock_llm.invoke.return_value = "The answer is 4."

        result = respond(self.state, self.mock_llm)

        assert result["context"] == self.context
        assert len(result["context"].messages) == 2
        assert result["context"].messages[-1]["content"] == "The answer is 4."
        assert result["context"].messages[-1]["role"] == "system"

    def test_respond_with_direct_response_json(self):
        """Test respond node with direct response JSON."""
        self.context.messages[-1][
            "content"
        ] = '{"action": "direct_response", "answer": "The answer is 4"}'

        result = respond(self.state, self.mock_llm)

        # Should replace JSON with clean answer, no LLM call
        assert result["context"].messages[-1]["content"] == "The answer is 4"
        self.mock_llm.invoke.assert_not_called()

    def test_respond_with_invalid_json(self):
        """Test respond node with invalid JSON."""
        self.context.messages[-1]["content"] = '{"invalid": json}'
        self.mock_llm.invoke.return_value = "I cannot parse that response."

        result = respond(self.state, self.mock_llm)

        # Should call LLM and replace message
        assert (
            result["context"].messages[-1]["content"] == "I cannot parse that response."
        )
        self.mock_llm.invoke.assert_called_once()

    def test_respond_with_conversation_history(self):
        """Test respond node uses conversation history."""
        # Change the system message to a non-JSON string to avoid parsing issues
        self.context.messages[-1]["content"] = "Calculator result: 4"
        self.mock_llm.invoke.return_value = "Based on the calculation, the answer is 4."

        respond(self.state, self.mock_llm)

        # Check that LLM was called with full conversation history plus system prompt
        call_args = self.mock_llm.invoke.call_args[0][0]
        assert len(call_args) >= 3  # System prompt + previous messages
        assert call_args[0]["role"] == "system"  # First should be system prompt
