"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.context import Context
from cogency.nodes.reason import build_iterations, reason
from cogency.state import State
from tests.conftest import MockLLM


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


def mock_context():
    context = Mock()
    context.messages = []
    context.chat = []
    context.query = "test query"
    context.add_message = Mock()
    return context


def mock_llm():
    llm = AsyncMock()
    llm.run = AsyncMock(
        return_value=Result(data='{"reasoning": "test reasoning", "strategy": "test_strategy"}')
    )
    return llm


def mock_tools():
    tool = Mock()
    tool.name = "test_tool"
    tool.schema = "test schema"
    tool.examples = []
    tool.rules = []
    return [tool]


def basic_state():
    return State(context=mock_context(), query="test query")


@pytest.mark.asyncio
async def test_cognition_initialization():
    state = basic_state()
    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert result.success
    state = result.data
    assert isinstance(state, State)
    # Cognition is now flattened into State
    assert hasattr(state, "current_approach")
    assert isinstance(state.iterations, list)
    assert hasattr(state, "failed_attempts")


@pytest.mark.asyncio
async def test_iteration_tracking():
    state = basic_state()
    state["iteration"] = 2

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert result.success
    state = result.data
    assert isinstance(state, State)
    assert state["iteration"] == 3


@pytest.mark.asyncio
async def test_max_iterations():
    state = basic_state()
    state["iteration"] = 5
    state["max_iterations"] = 5

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert result.success
    state = result.data
    assert isinstance(state, State)
    assert state["stop_reason"] == "max_iterations_reached"


@pytest.mark.asyncio
async def test_loop_detection():
    state = basic_state()
    # Set iterations directly on state (cognition is flattened)
    state.iterations = [
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
    state.react_mode = "deep"

    result = await reason(state, llm=mock_llm(), tools=mock_tools())
    assert result.success
    state = result.data
    assert isinstance(state, State)
    assert state.get("stop_reason") == "reasoning_loop_detected"


@pytest.mark.asyncio
async def test_llm_error():
    state = basic_state()
    llm = mock_llm()
    llm.run.side_effect = Exception("LLM error")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await reason(state, llm=llm, tools=mock_tools())
        assert not result.success
        assert "LLM error" in str(result.error)


@pytest.mark.asyncio
async def test_failed_attempts():
    state = basic_state()
    from resilient_result import Result

    state["result"] = Result(
        data={
            "success": True,
            "results": [],
            "successful_count": 0,
            "failed_count": 1,
        }
    )

    class DictLikeTool:
        def __init__(self, name, args):
            self.name = name
            self.args = args

        def get(self, key, default=None):
            if key == "function":
                return {"name": self.name}
            return default

    state["prev_tool_calls"] = [DictLikeTool("search", {"query": "test"})]

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert result.success
    state = result.data
    assert isinstance(state, State)
    # Check failed_attempts directly on state
    assert len(state.failed_attempts) == 1
    assert state.failed_attempts[0]["tool_calls"][0].name == "search"
    assert state.failed_attempts[0]["quality"] == "poor"


@pytest.mark.asyncio
async def test_memory_limit():
    state = basic_state()
    # Add many iterations to test memory limits
    for i in range(15):
        state.add_iteration(
            tool_calls=[{"name": f"tool{i}", "args": {}}],
            approach="test",
            decision="test",
            fingerprint=f"action{i}",
        )

    llm = mock_llm()
    llm.run.return_value = Result.ok(
        '{"thinking": "test", "decision": "new_decision", "tool_calls": [{"name": "test", "args": {}}]}'
    )

    result = await reason(state, llm=llm, tools=mock_tools())

    assert result.success
    state = result.data
    assert isinstance(state, State)
    # Check iterations directly on state with max_history limit (5)
    assert len(state.iterations) <= 5


def test_empty_fingerprints():
    state = basic_state()
    state.iterations = []
    state.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(state, [])

    assert result == "No previous iterations"


def test_basic_iterations():
    state = basic_state()
    state.iterations = [
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
    state.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(state, [], max_iterations=3)

    assert "PREVIOUS ITERATIONS:" in result
    assert "Iteration 1: search:hash1" in result
    assert "Iteration 2: files:hash2" in result
    assert "Iteration 3: calculate:hash3" in result


def test_truncation():
    state = basic_state()
    state.iterations = [
        {
            "iteration": i,
            "fingerprint": f"action{i}",
            "result": "",
            "decision": "",
            "tool_calls": [],
        }
        for i in range(1, 6)
    ]
    state.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(state, [], max_iterations=3)

    assert "PREVIOUS ITERATIONS:" in result
    assert "Iteration 3: action3" in result
    assert "Iteration 4: action4" in result
    assert "Iteration 5: action5" in result
    assert "action1" not in result
    assert "action2" not in result


def test_with_failures():
    state = basic_state()
    state.iterations = [
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
    state.failed_attempts = [
        {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
    ]

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
        result = build_iterations(state, [])

    assert "PREVIOUS ITERATIONS:" in result
    assert "Iteration 1: search:hash1" in result
    assert "Iteration 2: files:hash2" in result
    assert "FAILED ATTEMPTS:" in result
    assert "Previous failed attempts: 1 attempts failed" in result


def test_only_failures():
    state = basic_state()
    state.iterations = []
    state.failed_attempts = [
        {"tool_calls": [MockToolCall("search", {})], "quality": "failed", "iteration": 1}
    ]

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "Previous failed attempts: 1 attempts failed"
        result = build_iterations(state, [])

    assert result == "Previous failed attempts: 1 attempts failed"
    assert "PREVIOUS ITERATIONS:" not in result


def test_step_numbering():
    state = basic_state()
    state.iterations = [
        {"iteration": i, "fingerprint": f"a{i}", "result": "", "decision": "", "tool_calls": []}
        for i in range(1, 7)
    ]
    state.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(state, [], max_iterations=2)

    assert "Iteration 5: a5" in result
    assert "Iteration 6: a6" in result
    assert "Iteration 1:" not in result
    assert "Iteration 4:" not in result
