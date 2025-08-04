"""AgentState tests - Complete agent state composition."""

from cogency.state import AgentState
from cogency.state.user import UserProfile


def test_constructor():
    """Test AgentState constructor with minimal parameters."""
    state = AgentState(query="test query")

    assert state.execution.query == "test query"
    assert state.execution.user_id == "default"
    assert state.reasoning.goal == "test query"
    assert state.user is None


def test_with_user_id():
    """Test AgentState constructor with custom user_id."""
    state = AgentState(query="test query", user_id="custom_user")

    assert state.execution.query == "test query"
    assert state.execution.user_id == "custom_user"
    assert state.reasoning.goal == "test query"


def test_with_profile():
    """Test AgentState constructor with user profile."""
    profile = UserProfile(user_id="test_user")
    state = AgentState(query="test query", user_profile=profile)

    assert state.execution.query == "test query"
    assert state.user is profile
    assert state.user.user_id == "test_user"


def test_composition():
    """Test that AgentState properly composes all components."""
    state = AgentState(query="test query")

    # Has all required components
    assert hasattr(state, "execution")
    assert hasattr(state, "reasoning")
    assert hasattr(state, "user_profile")

    # Components are properly typed
    from cogency.state.execution import ExecutionState
    from cogency.state.reasoning import ReasoningContext

    assert isinstance(state.execution, ExecutionState)
    assert isinstance(state.reasoning, ReasoningContext)

    # Components are independent
    assert state.execution is not state.reasoning


def test_context_no_profile():
    """Test get_situated_context with no user profile."""
    state = AgentState(query="test query")

    context = state.get_situated_context()
    assert context == ""


def test_context_with_profile():
    """Test get_situated_context with user profile."""
    profile = UserProfile(user_id="test_user")
    # Add some test data to the profile
    profile.communication_style = "technical"
    profile.goals = ["complete project"]

    state = AgentState(query="test query", user_profile=profile)

    context = state.get_situated_context()
    assert context.startswith("USER CONTEXT:")


def test_update_thinking():
    """Test updating state from reasoning response with thinking."""
    state = AgentState(query="test query")

    reasoning_data = {
        "thinking": "I need to analyze this",
        "tool_calls": [{"name": "test_tool", "args": {}}],
    }

    state.update_from_reasoning(reasoning_data)

    # Should record thinking in reasoning context
    assert len(state.reasoning.thoughts) == 1
    assert state.reasoning.thoughts[0]["thinking"] == "I need to analyze this"

    # Should set tool calls in execution
    assert len(state.execution.pending_calls) == 1
    assert state.execution.pending_calls[0]["name"] == "test_tool"


def test_update_context():
    """Test updating reasoning context from reasoning response."""
    state = AgentState(query="test query")

    reasoning_data = {
        "context_updates": {
            "goal": "updated goal",
            "strategy": "new strategy",
            "insights": ["insight 1", "insight 2"],
        }
    }

    state.update_from_reasoning(reasoning_data)

    assert state.reasoning.goal == "updated goal"
    assert state.reasoning.strategy == "new strategy"
    assert "insight 1" in state.reasoning.insights
    assert "insight 2" in state.reasoning.insights


def test_update_response():
    """Test setting direct response from reasoning."""
    state = AgentState(query="test query")

    reasoning_data = {"response": "This is my response"}

    state.update_from_reasoning(reasoning_data)

    assert state.execution.response == "This is my response"


def test_update_mode():
    """Test switching execution mode from reasoning."""
    state = AgentState(query="test query")

    # Test valid mode switches
    for mode in ["fast", "deep", "adapt"]:
        reasoning_data = {"switch_mode": mode}
        state.update_from_reasoning(reasoning_data)
        assert state.execution.mode.value == mode

    # Test invalid mode switch is ignored
    old_mode = state.execution.mode
    reasoning_data = {"switch_mode": "invalid_mode"}
    state.update_from_reasoning(reasoning_data)
    assert state.execution.mode == old_mode


def test_update_empty():
    """Test updating with empty reasoning data."""
    state = AgentState(query="test query")

    # Should not crash with empty data
    state.update_from_reasoning({})

    # State should remain unchanged
    assert state.execution.response is None
    assert len(state.reasoning.thoughts) == 0
    assert len(state.execution.pending_calls) == 0


def test_update_comprehensive():
    """Test comprehensive reasoning update with all fields."""
    state = AgentState(query="test query")

    reasoning_data = {
        "thinking": "Complex analysis required",
        "tool_calls": [{"name": "analyze", "args": {"data": "test"}}],
        "context_updates": {
            "goal": "refined goal",
            "strategy": "comprehensive strategy",
            "insights": ["key insight"],
        },
        "response": "Final response",
        "switch_mode": "deep",
    }

    state.update_from_reasoning(reasoning_data)

    # All updates should be applied
    assert len(state.reasoning.thoughts) == 1
    assert state.reasoning.thoughts[0]["thinking"] == "Complex analysis required"
    assert len(state.execution.pending_calls) == 1
    assert state.reasoning.goal == "refined goal"
    assert state.reasoning.strategy == "comprehensive strategy"
    assert "key insight" in state.reasoning.insights
    assert state.execution.response == "Final response"
    assert state.execution.mode.value == "deep"


def test_state_independence():
    """Test that different AgentState instances are independent."""
    state1 = AgentState(query="query 1")
    state2 = AgentState(query="query 2")

    # Modify state1
    state1.execution.iteration = 5
    state1.reasoning.strategy = "strategy 1"

    # state2 should be unaffected
    assert state2.execution.iteration == 0
    assert state2.reasoning.strategy == ""
    assert state2.execution.query == "query 2"
