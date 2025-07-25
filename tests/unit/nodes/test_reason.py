"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.nodes.reason import build_iterations, reason
from cogency.state import Cognition, State
from tests.conftest import MockLLM


class MockToolCall:
    """Mock tool call for testing."""

    def __init__(self, name, args):
        self.name = name
        self.args = args


class TestReasonNode:
    """Test enhanced reason node functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        context = Mock()
        context.messages = []
        context.query = "test query"
        context.add_message = Mock()
        return context

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        llm = AsyncMock()
        llm.run = AsyncMock(
            return_value=Result(data='{"reasoning": "test reasoning", "strategy": "test_strategy"}')
        )
        return llm

    @pytest.fixture
    def mock_tools(self):
        """Create mock tools."""
        tool = Mock()
        tool.name = "test_tool"
        tool.schema = "test schema"
        tool.examples = []
        tool.rules = []
        return [tool]

    @pytest.fixture
    def basic_state(self, mock_context):
        """Create basic agent state."""
        from cogency.output import Output

        state = State(context=mock_context, query="test query", output=Output())
        return state

    @pytest.mark.asyncio
    async def test_cognition_initialization(self, basic_state, mock_llm, mock_tools):
        """Test that cognition gets initialized properly."""
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert isinstance(result, State)
        assert hasattr(result, "cognition")
        cognition = result.cognition
        assert hasattr(cognition, "current_approach")
        assert isinstance(cognition.iterations, list)
        assert hasattr(cognition, "failed_attempts")

    @pytest.mark.asyncio
    async def test_iteration_tracking(self, basic_state, mock_llm, mock_tools):
        """Test iteration counter increments."""
        basic_state["current_iteration"] = 2

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert isinstance(result, State)
        assert result["current_iteration"] == 3

    @pytest.mark.asyncio
    async def test_max_iterations_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops at max iterations."""
        basic_state["current_iteration"] = 5
        basic_state["MAX_ITERATIONS"] = 5

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert isinstance(result, State)
        assert result["stopping_reason"] == "max_iterations_reached"

    @pytest.mark.asyncio
    async def test_loop_detection_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops when loop detected."""
        cognition_obj = Cognition()
        cognition_obj.iterations = [
            {
                "iteration": 1,
                "fingerprint": "action1",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
            {
                "iteration": 2,
                "fingerprint": "action1",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
            {
                "iteration": 3,
                "fingerprint": "action1",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
        ]
        basic_state.cognition = cognition_obj
        basic_state.react_mode = "deep"

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        assert isinstance(result, State)
        assert result.get("stopping_reason") == "reasoning_loop_detected"

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_llm_error(self, basic_state, mock_llm, mock_tools):
        """Test graceful degradation when LLM fails."""
        mock_llm.run.side_effect = Exception("LLM error")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        # @safe.reasoning() decorator returns the modified state on success, error string on failure
        assert isinstance(result, State)
        # The safe decorator should handle the error gracefully

    @pytest.mark.asyncio
    async def test_failed_attempts_tracking(self, basic_state, mock_llm, mock_tools):
        """Test that failed attempts are tracked properly."""
        # Set up previous execution results indicating failure
        from cogency.utils.results import ActionResult

        basic_state["action_result"] = ActionResult(
            data={
                "success": True,
                "results": [],
                "successful_count": 0,
                "failed_count": 1,
            }
        )

        # Create a dict-like object that has name and args attributes
        class DictLikeTool:
            def __init__(self, name, args):
                self.name = name
                self.args = args

            def get(self, key, default=None):
                if key == "function":
                    return {"name": self.name}
                return default

        basic_state["prev_tool_calls"] = [DictLikeTool("search", {"query": "test"})]

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert isinstance(result, State)
        cognition = result.cognition
        assert len(cognition.failed_attempts) == 1
        assert cognition.failed_attempts[0]["tool_calls"][0].name == "search"
        assert cognition.failed_attempts[0]["quality"] == "poor"

    @pytest.mark.asyncio
    async def test_memory_limit_enforce(self, basic_state, mock_llm, mock_tools):
        """Test that memory limits are enforced."""
        # Create state with excessive history - fast mode limit is 3, deep mode is 10
        cognition_obj = Cognition()
        cognition_obj.max_history = 3  # Fast mode default
        cognition_obj.max_failures = 5
        for i in range(15):
            cognition_obj.update(
                tool_calls=[{"name": f"tool{i}", "args": {}}],
                current_approach="test",
                current_decision="test",
                action_fingerprint=f"action{i}",
            )
        basic_state.cognition = cognition_obj

        # Mock tool calls to trigger history update
        mock_llm.run.return_value = '{"thinking": "test", "decision": "new_decision", "tool_calls": [{"name": "test", "args": {}}]}'

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert isinstance(result, State)
        cognition = result.cognition
        # Should be limited by max_history setting (3 for fast mode)
        assert len(cognition.iterations) <= cognition.max_history


class TestBuildIterationHistory:
    """Test build_iterations function."""

    def test_empty_fingerprints_no_failures(self):
        """Test iteration history with empty cognition."""
        cognition = Cognition()
        cognition.iterations = []
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iterations(cognition, [])

        assert result == "No previous iterations"

    def test_basic_iterations(self):
        """Test basic iteration history building."""
        cognition = Cognition()
        cognition.iterations = [
            {
                "iteration": 1,
                "fingerprint": "search:hash1",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
            {
                "iteration": 2,
                "fingerprint": "files:hash2",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
            {
                "iteration": 3,
                "fingerprint": "calculate:hash3",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iterations(cognition, [], max_iterations=3)

        assert "PREVIOUS ITERATIONS:" in result
        assert "Iteration 1: search:hash1" in result
        assert "Iteration 2: files:hash2" in result
        assert "Iteration 3: calculate:hash3" in result

    def test_max_iterations_truncation(self):
        """Test that max_iterations limits shown history."""
        cognition = Cognition()
        cognition.iterations = [
            {
                "iteration": i,
                "fingerprint": f"action{i}",
                "result": "",
                "decision": "",
                "tool_calls": [],
            }
            for i in range(1, 6)
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iterations(cognition, [], max_iterations=3)

        assert "PREVIOUS ITERATIONS:" in result
        assert "Iteration 3: action3" in result  # Shows last 3 iterations
        assert "Iteration 4: action4" in result
        assert "Iteration 5: action5" in result
        assert "action1" not in result  # Older actions truncated
        assert "action2" not in result

    def test_with_failures_included(self):
        """Test iteration history includes failed attempts."""
        cognition = Cognition()
        cognition.iterations = [
            {
                "iteration": 1,
                "fingerprint": "search:hash1",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
            {
                "iteration": 2,
                "fingerprint": "files:hash2",
                "result": "",
                "decision": "",
                "tool_calls": [],
            },
        ]
        cognition.failed_attempts = [
            {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
        ]

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
            result = build_iterations(cognition, [])

        assert "PREVIOUS ITERATIONS:" in result
        assert "Iteration 1: search:hash1" in result
        assert "Iteration 2: files:hash2" in result
        assert "FAILED ATTEMPTS:" in result
        assert "Previous failed attempts: 1 attempts failed" in result

    def test_only_failures_no_fingerprints(self):
        """Test when only failures exist without successful iterations."""
        cognition = Cognition()
        cognition.iterations = []
        cognition.failed_attempts = [
            {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
        ]

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
            result = build_iterations(cognition, [])

        assert result == "Previous failed attempts: 1 attempts failed"
        assert "PREVIOUS ITERATIONS:" not in result

    def test_step_numbering_calculation(self):
        """Test correct step numbering when truncating history."""
        cognition = Cognition()
        cognition.iterations = [
            {"iteration": i, "fingerprint": f"a{i}", "result": "", "decision": "", "tool_calls": []}
            for i in range(1, 7)
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iterations(cognition, [], max_iterations=2)

        # Should show iterations 5 and 6 (last 2 of 6 total)
        assert "Iteration 5: a5" in result
        assert "Iteration 6: a6" in result
        assert "Iteration 1:" not in result
        assert "Iteration 4:" not in result
