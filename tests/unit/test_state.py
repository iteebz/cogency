"""State tests."""

from cogency.context import Context
from cogency.output import Output
from cogency.state import Cognition, State, summarize_attempts


def mock_context():
    return Context("test")


def mock_tool_call(name, args):
    return {"name": name, "args": args}


def test_state_creation():
    context = mock_context()
    state = State(context=context, query="test query", output=Output())

    assert state["context"] == context
    assert state["query"] == "test query"
    assert isinstance(state["output"], Output)


def test_dict_access():
    context = mock_context()
    state = State(context=context, query="test query", output=Output())

    assert "context" in state
    assert "query" in state
    assert "output" in state

    assert state.get("context") == context
    assert state.get("nonexistent") is None

    state["new_field"] = "test_value"
    assert state["new_field"] == "test_value"


def test_cognition_property():
    context = mock_context()
    state = State(context=context, query="test query", output=Output())

    assert isinstance(state.cognition, Cognition)
    assert state.cognition.react_mode == "fast"


def test_cognition_update():
    cognition = Cognition()
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    cognition.update(tool_calls, "analytical", "search for info", "search:123", "Found 3 results")

    assert cognition.current_approach == "analytical"
    assert len(cognition.iterations) == 1
    assert cognition.iterations[0]["fingerprint"] == "search:123"
    assert cognition.iterations[0]["decision"] == "search for info"
    assert cognition.iterations[0]["result"] == "Found 3 results"


def test_cognition_update_result():
    cognition = Cognition()
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    cognition.update(tool_calls, "analytical", "search for info", "search:123", "")
    assert cognition.iterations[0]["result"] == ""

    cognition.update_result("Found 3 relevant documents")
    assert cognition.iterations[0]["result"] == "Found 3 relevant documents"


def test_track_failure():
    cognition = Cognition()
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    cognition.track_failure(tool_calls, "poor", 2)

    assert len(cognition.failed_attempts) == 1
    failure = cognition.failed_attempts[0]
    assert failure["tool_calls"] == tool_calls
    assert failure["quality"] == "poor"
    assert failure["iteration"] == 2


def test_tool_quality_tracking():
    cognition = Cognition()

    assert cognition.last_tool_quality == "unknown"

    cognition.set_tool_quality("excellent")
    assert cognition.last_tool_quality == "excellent"


def test_mode_switching():
    cognition = Cognition("fast")
    assert cognition.react_mode == "fast"

    cognition.switch_mode("deep", "complex problem detected")
    assert cognition.react_mode == "deep"
    assert len(cognition.mode_switches) == 1

    switch = cognition.mode_switches[0]
    assert switch["from"] == "fast"
    assert switch["to"] == "deep"
    assert switch["reason"] == "complex problem detected"


def test_summarize_attempts():
    summary = summarize_attempts([])
    assert summary == "No previous failed attempts"

    failed_attempts = [
        {
            "tool_calls": [{"name": "search", "args": {"query": "test1"}}],
            "quality": "poor",
            "iteration": 1,
        },
        {
            "tool_calls": [
                {"name": "search", "args": {"query": "test2"}},
                {"name": "scrape", "args": {"url": "http://example.com"}},
            ],
            "quality": "failed",
            "iteration": 2,
        },
    ]

    summary = summarize_attempts(failed_attempts)
    assert "2 attempts failed" in summary
    assert "search (poor)" in summary
    assert "search, scrape (failed)" in summary

    many_attempts = [
        {"tool_calls": [{"name": "tool1", "args": {}}], "quality": "poor", "iteration": 1},
        {"tool_calls": [{"name": "tool2", "args": {}}], "quality": "failed", "iteration": 2},
        {"tool_calls": [{"name": "tool3", "args": {}}], "quality": "poor", "iteration": 3},
        {"tool_calls": [{"name": "tool4", "args": {}}], "quality": "failed", "iteration": 4},
    ]

    summary = summarize_attempts(many_attempts)
    assert "4 attempts failed" in summary
    assert "tool2 (failed)" in summary
    assert "tool3 (poor)" in summary
    assert "tool4 (failed)" in summary
    assert "tool1" not in summary
