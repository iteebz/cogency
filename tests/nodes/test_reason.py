"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.nodes.reason import build_iteration_history, reason
from cogency.state import Cognition, State


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
            return_value='{"reasoning": "test reasoning", "strategy": "test_strategy"}'
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

        assert hasattr(result, "cognition")
        cognition = result.cognition
        assert hasattr(cognition, "current_approach")
        assert isinstance(cognition.action_fingerprints, list)
        assert hasattr(cognition, "failed_attempts")

    @pytest.mark.asyncio
    async def test_iteration_tracking(self, basic_state, mock_llm, mock_tools):
        """Test iteration counter increments."""
        basic_state["current_iteration"] = 2

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert result["current_iteration"] == 3

    @pytest.mark.asyncio
    async def test_max_iterations_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops at max iterations."""
        basic_state["current_iteration"] = 5
        basic_state["max_iterations"] = 5

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert result["stopping_reason"] == "max_iterations_reached"

    @pytest.mark.asyncio
    async def test_loop_detection_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops when loop detected."""
        cognition_obj = Cognition()
        cognition_obj.action_fingerprints = [
            {"fingerprint": "action1", "result": "", "decision": ""},
            {"fingerprint": "action1", "result": "", "decision": ""},
            {"fingerprint": "action1", "result": "", "decision": ""},
        ]
        basic_state.cognition = cognition_obj

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert result.get("stopping_reason") == "reasoning_loop_detected"

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_llm_error(self, basic_state, mock_llm, mock_tools):
        """Test graceful degradation when LLM fails."""
        mock_llm.run.side_effect = Exception("LLM error")

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        assert result["can_answer_directly"] is True
        assert result["tool_calls"] is None
        assert "issue" in result["reasoning_response"]

    @pytest.mark.asyncio
    async def test_failed_attempts_tracking(self, basic_state, mock_llm, mock_tools):
        """Test that failed attempts are tracked properly."""
        # Set up previous execution results indicating failure
        from cogency.utils.results import ExecutionResult

        basic_state["execution_results"] = ExecutionResult(
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

        cognition = result.cognition
        assert len(cognition.failed_attempts) == 1
        assert cognition.failed_attempts[0]["tool_calls"][0].name == "search"
        assert cognition.failed_attempts[0]["quality"] == "poor"

    @pytest.mark.asyncio
    async def test_memory_limit_enforce(self, basic_state, mock_llm, mock_tools):
        """Test that memory limits are enforced."""
        # Create state with excessive history - fast mode limit is 3, deep mode is 10
        cognition_obj = Cognition()
        cognition_obj.action_fingerprints = [
            {"fingerprint": f"action{i}", "result": "", "decision": ""} for i in range(15)
        ]
        cognition_obj.failed_attempts = []
        cognition_obj.max_history = 3  # Fast mode default
        cognition_obj.max_failures = 5
        basic_state.cognition = cognition_obj

        # Mock tool calls to trigger history update
        mock_llm.run.return_value = '{"thinking": "test", "decision": "new_decision", "tool_calls": [{"name": "test", "args": {}}]}'

        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)

        cognition = result.cognition
        # Should be limited by max_history setting (3 for fast mode)
        assert len(cognition.action_fingerprints) <= cognition.max_history


class TestBuildIterationHistory:
    """Test build_iteration_history function."""

    def test_empty_fingerprints_no_failures(self):
        """Test iteration history with empty cognition."""
        cognition = Cognition()
        cognition.action_fingerprints = []
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iteration_history(cognition, [])

        assert result == "No previous iterations"

    def test_basic_iteration_history(self):
        """Test basic iteration history building."""
        cognition = Cognition()
        cognition.action_fingerprints = [
            {"fingerprint": "search:hash1", "result": "", "decision": ""},
            {"fingerprint": "files:hash2", "result": "", "decision": ""},
            {"fingerprint": "calculate:hash3", "result": "", "decision": ""},
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iteration_history(cognition, [], max_iterations=3)

        assert "PREVIOUS ITERATIONS:" in result
        assert "Step 1: search:hash1" in result
        assert "Step 2: files:hash2" in result
        assert "Step 3: calculate:hash3" in result

    def test_max_iterations_truncation(self):
        """Test that max_iterations limits shown history."""
        cognition = Cognition()
        cognition.action_fingerprints = [
            {"fingerprint": f"action{i}", "result": "", "decision": ""} for i in range(1, 6)
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iteration_history(cognition, [], max_iterations=3)

        assert "PREVIOUS ITERATIONS:" in result
        assert "Step 3: action3" in result  # Shows last 3 starting from step 3
        assert "Step 4: action4" in result
        assert "Step 5: action5" in result
        assert "action1" not in result  # Older actions truncated
        assert "action2" not in result

    def test_with_failures_included(self):
        """Test iteration history includes failed attempts."""
        cognition = Cognition()
        cognition.action_fingerprints = [
            {"fingerprint": "search:hash1", "result": "", "decision": ""},
            {"fingerprint": "files:hash2", "result": "", "decision": ""},
        ]
        cognition.failed_attempts = [
            {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
        ]

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
            result = build_iteration_history(cognition, [])

        assert "PREVIOUS ITERATIONS:" in result
        assert "Step 1: search:hash1" in result
        assert "Step 2: files:hash2" in result
        assert "FAILED ATTEMPTS:" in result
        assert "Previous failed attempts: 1 attempts failed" in result

    def test_only_failures_no_fingerprints(self):
        """Test when only failures exist without successful iterations."""
        cognition = Cognition()
        cognition.action_fingerprints = []
        cognition.failed_attempts = [
            {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
        ]

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
            result = build_iteration_history(cognition, [])

        assert result == "Previous failed attempts: 1 attempts failed"
        assert "PREVIOUS ITERATIONS:" not in result

    def test_step_numbering_calculation(self):
        """Test correct step numbering when truncating history."""
        cognition = Cognition()
        cognition.action_fingerprints = [
            {"fingerprint": f"a{i}", "result": "", "decision": ""} for i in range(1, 7)
        ]
        cognition.failed_attempts = []

        with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
            mock_summarize.return_value = "No previous failed attempts"
            result = build_iteration_history(cognition, [], max_iterations=2)

        # Should show steps 5 and 6 (last 2 of 6 total)
        assert "Step 5: a5" in result
        assert "Step 6: a6" in result
        assert "Step 1:" not in result
        assert "Step 4:" not in result
