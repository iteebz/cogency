"""State tests - unified dict-based State."""

from cogency.context import Context
from cogency.state import State, summarize_attempts


def mock_context():
    return Context("test")


def mock_tool_call(name, args):
    return {"name": name, "args": args}


def test_state_creation():
    """Test creating a State instance."""
    context = mock_context()
    state = State(context=context, query="test query")

    assert state["context"] == context
    assert state["query"] == "test query"
    assert state.context == context
    assert state.query == "test query"


def test_dict_access():
    """Test dict-like access patterns."""
    context = mock_context()
    state = State(context=context, query="test query")

    assert "context" in state
    assert "query" in state
    assert "iteration" in state

    assert state.get("context") == context
    assert state.get("nonexistent") is None

    state["new_field"] = "test_value"
    assert state["new_field"] == "test_value"
    assert state.new_field == "test_value"


def test_dot_notation_access():
    """Test dot notation access to dict keys."""
    context = mock_context()
    state = State(context=context, query="test query")

    assert state.iteration == 0
    assert state.react_mode == "fast"
    assert state.tool_calls == []

    state.iteration = 5
    assert state["iteration"] == 5
    assert state.iteration == 5


def test_default_values():
    """Test that default values are properly set."""
    context = mock_context()
    state = State(context=context, query="test query")

    assert state.iteration == 0
    assert state.max_iterations == 12
    assert state.react_mode == "fast"
    assert state.tool_calls == []
    assert state.selected_tools == []
    assert state.tool_failures == 0
    assert state.quality_retries == 0
    assert state.tool_retries == 0
    assert state.direct_answer is False
    assert state.stop_reason is None
    assert state.reasoning is None
    assert state.response is None
    assert state.iterations == []
    assert state.failed_attempts == []
    assert state.mode_switches == []
    assert state.preserved_context == ""
    assert state.last_tool_quality == "unknown"
    assert state.current_approach == "initial"
    assert state.notifications == []
    assert state.verbose is False


def test_update_cognition():
    """Test cognition update functionality."""
    context = mock_context()
    state = State(context=context, query="test query")
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    state.update_cognition(
        tool_calls, "analytical", "search for info", "search:123", "Found 3 results"
    )

    assert state.current_approach == "analytical"
    assert len(state.iterations) == 1
    assert state.iterations[0]["fingerprint"] == "search:123"
    assert state.iterations[0]["decision"] == "search for info"
    assert state.iterations[0]["result"] == "Found 3 results"


def test_update_result():
    """Test updating the last iteration's result."""
    context = mock_context()
    state = State(context=context, query="test query")
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    state.update_cognition(tool_calls, "analytical", "search for info", "search:123", "")
    assert state.iterations[0]["result"] == ""

    state.update_result("Found 3 relevant documents")
    assert state.iterations[0]["result"] == "Found 3 relevant documents"


def test_track_failure():
    """Test tracking failed tool attempts."""
    context = mock_context()
    state = State(context=context, query="test query")
    tool_calls = [mock_tool_call("search", {"query": "test"})]

    state.track_failure(tool_calls, "poor")

    assert len(state.failed_attempts) == 1
    failure = state.failed_attempts[0]
    assert failure["tool_calls"] == tool_calls
    assert failure["quality"] == "poor"
    assert failure["iteration"] == 0


def test_tool_quality_tracking():
    """Test tool quality tracking."""
    context = mock_context()
    state = State(context=context, query="test query")

    assert state.last_tool_quality == "unknown"

    state.last_tool_quality = "excellent"
    assert state.last_tool_quality == "excellent"


def test_mode_switching():
    """Test mode switching functionality."""
    context = mock_context()
    state = State(context=context, query="test query")
    assert state.react_mode == "fast"

    state.switch_mode("deep", "complex problem detected")
    assert state.react_mode == "deep"
    assert len(state.mode_switches) == 1

    switch = state.mode_switches[0]
    assert switch["from"] == "fast"
    assert switch["to"] == "deep"
    assert switch["reason"] == "complex problem detected"


def test_kwargs_support():
    """Test that additional kwargs are properly handled."""
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, custom_field="custom_value")

    assert state.verbose is True
    assert state.custom_field == "custom_value"


def test_summarize_attempts():
    """Test the summarize_attempts utility function."""
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
