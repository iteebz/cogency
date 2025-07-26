"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.nodes.reason import build_iterations, reason
from cogency.state import Cognition, State
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
    from cogency.output import Output

    return State(context=mock_context(), query="test query", output=Output())


@pytest.mark.asyncio
async def test_cognition_initialization():
    state = basic_state()
    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert isinstance(result, State)
    assert hasattr(result, "cognition")
    cognition = result.cognition
    assert hasattr(cognition, "current_approach")
    assert isinstance(cognition.iterations, list)
    assert hasattr(cognition, "failed_attempts")


@pytest.mark.asyncio
async def test_iteration_tracking():
    state = basic_state()
    state["iteration"] = 2

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert isinstance(result, State)
    assert result["iteration"] == 3


@pytest.mark.asyncio
async def test_max_iterations():
    state = basic_state()
    state["iteration"] = 5
    state["MAX_ITERATIONS"] = 5

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert isinstance(result, State)
    assert result["stop_reason"] == "max_iterations_reached"


@pytest.mark.asyncio
async def test_loop_detection():
    state = basic_state()
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
    state.cognition = cognition_obj
    state.react_mode = "deep"

    result = await reason(state, llm=mock_llm(), tools=mock_tools())
    assert isinstance(result, State)
    assert result.get("stop_reason") == "reasoning_loop_detected"


@pytest.mark.asyncio
async def test_llm_error():
    state = basic_state()
    llm = mock_llm()
    llm.run.side_effect = Exception("LLM error")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await reason(state, llm=llm, tools=mock_tools())

    assert isinstance(result, State)


@pytest.mark.asyncio
async def test_failed_attempts():
    state = basic_state()
    from cogency.utils.results import Result

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

    assert isinstance(result, State)
    cognition = result.cognition
    assert len(cognition.failed_attempts) == 1
    assert cognition.failed_attempts[0]["tool_calls"][0].name == "search"
    assert cognition.failed_attempts[0]["quality"] == "poor"


@pytest.mark.asyncio
async def test_memory_limit():
    state = basic_state()
    cognition_obj = Cognition()
    cognition_obj.max_history = 3
    cognition_obj.max_failures = 5
    for i in range(15):
        cognition_obj.update(
            tool_calls=[{"name": f"tool{i}", "args": {}}],
            current_approach="test",
            current_decision="test",
            action_fingerprint=f"action{i}",
        )
    state.cognition = cognition_obj

    llm = mock_llm()
    llm.run.return_value = '{"thinking": "test", "decision": "new_decision", "tool_calls": [{"name": "test", "args": {}}]}'

    result = await reason(state, llm=llm, tools=mock_tools())

    assert isinstance(result, State)
    cognition = result.cognition
    assert len(cognition.iterations) <= cognition.max_history


def test_empty_fingerprints():
    cognition = Cognition()
    cognition.iterations = []
    cognition.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(cognition, [])

    assert result == "No previous iterations"


def test_basic_iterations():
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


def test_truncation():
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
    assert "Iteration 3: action3" in result
    assert "Iteration 4: action4" in result
    assert "Iteration 5: action5" in result
    assert "action1" not in result
    assert "action2" not in result


def test_with_failures():
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


def test_only_failures():
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


def test_step_numbering():
    cognition = Cognition()
    cognition.iterations = [
        {"iteration": i, "fingerprint": f"a{i}", "result": "", "decision": "", "tool_calls": []}
        for i in range(1, 7)
    ]
    cognition.failed_attempts = []

    with patch("cogency.nodes.reason.summarize_attempts") as mock_summarize:
        mock_summarize.return_value = "No previous failed attempts"
        result = build_iterations(cognition, [], max_iterations=2)

    assert "Iteration 5: a5" in result
    assert "Iteration 6: a6" in result
    assert "Iteration 1:" not in result
    assert "Iteration 4:" not in result
