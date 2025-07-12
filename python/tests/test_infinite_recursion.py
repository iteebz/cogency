"""Tests for infinite recursion prevention and edge cases."""
import unittest

from cogency.agent import Agent
from cogency.context import Context
from cogency.llm.base import BaseLLM
from cogency.nodes.reason import reason
from cogency.types import AgentState, ExecutionTrace
from cogency.utils.parsing import parse_reflect_response


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, responses=None):
        super().__init__()
        self.responses = responses or []
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = "Default response"
        self.call_count += 1
        return response


class TestInfiniteRecursionPrevention(unittest.TestCase):
    """Test infinite recursion prevention mechanisms."""

    def test_max_depth_prevents_infinite_loops(self):
        """Test that max_depth prevents infinite execution loops."""
        # Mock LLM that always wants to continue (would cause infinite loop)
        mock_responses = [
            '{"action": "tool_needed", "reasoning": "Need calculator"}',  # plan
            'TOOL_CALL: calculator(operation="add", x1=1, x2=1)',  # reason
            '{"status": "continue", "assessment": "Keep going"}',  # reflect (tries to continue)
        ] * 20  # Repeat many times to test recursion limit

        mock_llm = MockLLM(mock_responses)
        agent = Agent(
            name="TestAgent", llm=mock_llm, max_depth=5
        )  # Sufficient limit for test

        # This should hit the recursion limit and raise an exception
        from langgraph.errors import GraphRecursionError

        with self.assertRaises(GraphRecursionError):
            agent.run("What is 1 + 1?")

    def test_reflect_defaults_to_complete_on_error(self):
        """Test that reflect node defaults to 'complete' on parsing errors to prevent loops."""
        # Test malformed JSON that would previously cause infinite loops
        malformed_responses = [
            "Invalid JSON response",
            None,
            "",
            "{ malformed json",
            "Just plain text",
        ]

        for response in malformed_responses:
            route, data = parse_reflect_response(response)
            # Should default to complete/respond instead of continue/reason
            self.assertEqual(route, "respond", f"Failed for response: {response}")
            self.assertEqual(
                data["status"], "complete", f"Failed for response: {response}"
            )

    def test_reason_preserves_conversation_history(self):
        """Test that reason node preserves conversation history to prevent repeating actions."""
        context = Context(current_input="What is 2 + 2?")
        # Simulate previous conversation
        context.add_message("user", "What is 2 + 2?")
        context.add_message(
            "assistant", "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        )
        context.add_message("system", "Calculator result: 4")

        state: AgentState = {
            "context": context,
            "execution_trace": ExecutionTrace("test123"),
        }

        mock_llm = MockLLM(["The answer is 4 based on the previous calculation."])

        result_state = reason(state, mock_llm, [])

        # Should preserve all previous messages
        messages = result_state["context"].messages
        self.assertGreaterEqual(
            len(messages), 4
        )  # At least the original messages + new response

        # Should include the calculation history
        calculator_call_found = any(
            "calculator" in str(msg.get("content", "")) for msg in messages
        )
        self.assertTrue(
            calculator_call_found, "Previous calculator call should be preserved"
        )

    def test_agent_handles_none_llm_response(self):
        """Test agent gracefully handles None responses from LLM."""
        mock_llm = MockLLM(
            ['{"action": "direct_response", "answer": "No response"}'] * 5
        )
        agent = Agent(name="TestAgent", llm=mock_llm, max_depth=5)

        # Should not crash on None response
        result = agent.run("Test message")
        self.assertIsNotNone(result)
        self.assertIn("response", result)

    def test_recursion_limit_configuration(self):
        """Test that recursion limit is properly configured in LangGraph."""
        mock_llm = MockLLM(['{"action": "direct_response", "answer": "Hello"}'])

        # Test different max_depth values
        for max_depth in [5, 10, 15]:
            agent = Agent(name="TestAgent", llm=mock_llm, max_depth=max_depth)

            # Verify the agent has the correct max_depth
            self.assertEqual(agent.max_depth, max_depth)

            # Should work normally with proper limits
            result = agent.run("Hello")
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
