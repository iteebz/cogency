"""State tests - Split-State Model architecture."""

from cogency.state import State
from cogency.state.agent import ExecutionState, UserProfile, Workspace


def test_constructor():
    """Test State constructor with minimal parameters."""
    state = State(query="test query")

    assert state.query == "test query"
    assert state.user_id == "default"
    assert state.profile.user_id == "default"
    assert state.workspace.objective == "test query"
    assert state.execution is not None


def test_with_user_id():
    """Test State constructor with custom user_id."""
    state = State(query="test query", user_id="custom_user")

    assert state.query == "test query"
    assert state.user_id == "custom_user"
    assert state.profile.user_id == "custom_user"


def test_with_profile():
    """Test State constructor with user profile."""
    profile = UserProfile(user_id="test_user")
    state = State(query="test query", profile=profile)

    assert state.query == "test query"
    assert state.profile is profile
    assert state.profile.user_id == "test_user"


def test_split_state_composition():
    """Test that State properly implements Split-State Model."""
    state = State(query="test query")

    # Has all required layers
    assert hasattr(state, "profile")  # Persistent across sessions
    assert hasattr(state, "workspace")  # Ephemeral task state
    assert hasattr(state, "execution")  # Runtime-only mechanics

    # Components are properly typed
    assert isinstance(state.profile, UserProfile)
    assert isinstance(state.workspace, Workspace)
    assert isinstance(state.execution, ExecutionState)

    # Components are independent
    assert state.profile is not state.workspace
    assert state.workspace is not state.execution
    assert state.execution is not state.profile


def test_profile_layer():
    """Test UserProfile layer - persistent across sessions."""
    state = State(query="test query")

    # Profile is initialized with user_id
    assert state.profile.user_id == "default"
    assert isinstance(state.profile.preferences, dict)
    assert isinstance(state.profile.goals, list)
    assert isinstance(state.profile.expertise_areas, list)


def test_workspace_layer():
    """Test Workspace layer - ephemeral task state."""
    state = State(query="test query")

    # Workspace objective is set from query
    assert state.workspace.objective == "test query"
    assert isinstance(state.workspace.observations, list)
    assert isinstance(state.workspace.insights, list)
    assert isinstance(state.workspace.facts, dict)


def test_execution_layer():
    """Test ExecutionState layer - runtime-only mechanics."""
    state = State(query="test query")

    # Execution state is properly initialized
    assert state.execution.iteration == 0
    assert state.execution.mode == "adapt"
    assert isinstance(state.execution.messages, list)
    assert isinstance(state.execution.pending_calls, list)


def test_state_independence():
    """Test that different State instances are independent."""
    state1 = State(query="query 1")
    state2 = State(query="query 2")

    # Modify state1
    state1.execution.iteration = 5
    state1.workspace.assessment = "assessment 1"
    state1.profile.communication_style = "technical"

    # state2 should be unaffected
    assert state2.execution.iteration == 0
    assert state2.workspace.assessment == ""
    assert state2.profile.communication_style == ""
    assert state2.query == "query 2"


def test_post_init_behavior():
    """Test __post_init__ initialization behavior."""
    # Test with no profile
    state = State(query="test query", user_id="alice")
    assert state.profile.user_id == "alice"
    assert state.workspace.objective == "test query"
    assert state.execution is not None

    # Test with existing profile
    profile = UserProfile(user_id="bob")
    state = State(query="another query", profile=profile)
    assert state.profile is profile
    assert state.profile.user_id == "bob"


def test_semantic_boundaries():
    """Test semantic time horizons are properly isolated."""
    state = State(query="test query")

    # Profile: persistent across sessions
    state.profile.preferences["theme"] = "dark"
    state.profile.goals.append("learn python")

    # Workspace: ephemeral task state
    state.workspace.insights.append("need to refactor")
    state.workspace.facts["api_key"] = "test123"

    # Execution: runtime-only mechanics
    state.execution.messages.append({"role": "user", "content": "hello"})
    state.execution.iteration = 3

    # All layers should contain their respective data
    assert "theme" in state.profile.preferences
    assert "need to refactor" in state.workspace.insights
    assert len(state.execution.messages) == 1
    assert state.execution.iteration == 3
