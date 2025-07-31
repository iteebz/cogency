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
    # Cognitive workspace fields
    assert state.objective == ""
    assert state.assessment == ""
    assert state.approach == ""
    assert state.observations == ""
    assert state.response is None
    assert state.notify is True
    assert state.debug is False
    assert state.callback is None
    assert state.notifications == []


def test_kwargs():
    """Test that additional kwargs are properly handled."""
    state = State(query="test query", notify=True)
    assert state.notify is True


def test_update():
    """Test updating cognitive workspace fields."""
    state = State(query="test query")

    # Test workspace update method
    workspace_update = {
        "objective": "Test the cognitive workspace",
        "assessment": "We know this is a test",
        "approach": "Use update_workspace method",
        "observations": "The workspace update works",
    }

    state.update_workspace(workspace_update)

    assert state.objective == "Test the cognitive workspace"
    assert state.assessment == "We know this is a test"
    assert state.approach == "Use update_workspace method"
    assert state.observations == "The workspace update works"
