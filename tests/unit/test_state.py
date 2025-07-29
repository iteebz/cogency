"""State tests - dataclass-based State."""

from cogency.state import State


def test_state_creation():
    """Test creating a State instance."""
    state = State(query="test query")
    assert state.query == "test query"


def test_attribute_access():
    """Test attribute access patterns."""
    state = State(query="test query")

    assert hasattr(state, "query")
    assert hasattr(state, "iteration")
    assert getattr(state, "nonexistent", None) is None

    state.iteration = 1
    assert state.iteration == 1


def test_dot_notation_access():
    """Test dot notation access to state attributes."""
    state = State(query="test query")

    assert state.iteration == 0
    assert state.react_mode == "fast"
    assert state.tool_calls == []

    state.iteration = 5
    assert state.iteration == 5


def test_default_values():
    """Test that default values are properly set."""
    state = State(query="test query")

    assert state.user_id == "default"
    assert state.messages == []
    assert state.iteration == 0
    assert state.depth == 3
    assert state.react_mode == "fast"
    assert state.stop_reason is None
    assert state.selected_tools == []
    assert state.tool_calls == []
    assert state.result is None
    assert state.actions == []
    assert state.attempts == []
    assert state.situation_summary == {
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


def test_kwargs_support():
    """Test that additional kwargs are properly handled."""
    state = State(query="test query", notify=True)
    assert state.notify is True


def test_state_update():
    """Test updating a state attribute."""
    state = State(query="test query")
    assert state.situation_summary == {
        "goal": "",
        "progress": "",
        "current_approach": "",
        "key_findings": "",
        "next_focus": "",
    }
    state.situation_summary = {"summary": "The user wants to test the state."}
    assert state.situation_summary == {"summary": "The user wants to test the state."}
