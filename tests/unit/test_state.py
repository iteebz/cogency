"""State tests - dataclass-based State."""

from cogency.state import State


def test_create():
    """Test creating a State instance."""
    state = State(query="test query")
    assert state.query == "test query"


def test_attrs():
    """Test attribute access patterns."""
    state = State(query="test query")

    assert hasattr(state, "query")
    assert hasattr(state, "iteration")
    assert getattr(state, "nonexistent", None) is None

    state.iteration = 1
    assert state.iteration == 1


def test_dot():
    """Test dot notation access to state attributes."""
    state = State(query="test query")

    assert state.iteration == 0
    assert state.mode == "fast"
    assert state.tool_calls == []

    state.iteration = 5
    assert state.iteration == 5


def test_defaults():
    """Test that default values are properly set."""
    state = State(query="test query")

    assert state.user_id == "default"
    assert state.messages == []
    assert state.iteration == 0
    assert state.depth == 10
    assert state.mode == "fast"
    assert state.stop_reason is None
    assert state.selected_tools == []
    assert state.tool_calls == []
    assert state.result is None
    assert state.actions == []
    assert state.attempts == []
    assert state.summary == {
        "goal": "",
        "progress": "",
        "current_approach": "",
        "key_findings": "",
        "next_focus": "",
    }
    assert state.response is None
    assert state.respond_directly is False
    assert state.notify is True
    assert state.debug is False
    assert state.callback is None
    assert state.notifications == []


def test_kwargs():
    """Test that additional kwargs are properly handled."""
    state = State(query="test query", notify=True)
    assert state.notify is True


def test_update():
    """Test updating a state attribute."""
    state = State(query="test query")
    assert state.summary == {
        "goal": "",
        "progress": "",
        "current_approach": "",
        "key_findings": "",
        "next_focus": "",
    }
    state.summary = {"summary": "The user wants to test the state."}
    assert state.summary == {"summary": "The user wants to test the state."}
