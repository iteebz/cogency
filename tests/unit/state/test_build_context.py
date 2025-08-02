"""Context building tests - Comprehensive context assembly."""

from cogency.memory import compress_for_injection
from cogency.state import AgentState
from cogency.state.reasoning import ReasoningContext
from cogency.state.user_profile import UserProfile


def test_reasoning_context_compression():
    """Test reasoning context compression for LLM context."""
    context = ReasoningContext(goal="test goal", strategy="test strategy")
    context.add_insight("key insight")
    context.update_facts("important_fact", "fact_value")
    context.record_thinking("complex analysis", [{"tool": "test"}])

    compressed = context.compress_for_context()

    assert "GOAL: test goal" in compressed
    assert "STRATEGY: test strategy" in compressed
    assert "FACTS: important_fact: fact_value" in compressed
    assert "INSIGHTS: key insight" in compressed
    assert "LAST THINKING: complex analysis" in compressed


def test_user_profile_context_injection():
    """Test user profile context for agent initialization."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "technical"
    profile.goals = ["complete project", "learn skills"]
    profile.expertise_areas = ["python", "ml"]
    profile.projects = {"current": "test project"}

    context = compress_for_injection(profile)

    assert "COMMUNICATION: technical" in context
    assert "CURRENT GOALS:" in context
    assert "EXPERTISE: python, ml" in context
    assert "ACTIVE PROJECTS: current: test project" in context


def test_agent_state_situated_context():
    """Test AgentState situated context building."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "concise"
    profile.goals = ["efficiency"]

    state = AgentState(query="test query", user_profile=profile)

    situated_context = state.get_situated_context()

    assert situated_context.startswith("USER CONTEXT:")
    assert "COMMUNICATION: concise" in situated_context
    assert "CURRENT GOALS: efficiency" in situated_context


def test_comprehensive_context_building():
    """Test building comprehensive context from all components."""
    # Create user profile with rich context
    profile = UserProfile(user_id="expert_user")
    profile.communication_style = "technical and detailed"
    profile.goals = ["optimize performance", "maintain code quality"]
    profile.expertise_areas = ["python", "distributed systems", "optimization"]
    profile.projects = {"current": "high-performance service"}
    profile.preferences = {"format": "structured", "detail_level": "high"}

    # Create agent state
    state = AgentState(query="optimize database queries", user_profile=profile)

    # Add reasoning context
    state.reasoning.strategy = "analyze bottlenecks then optimize"
    state.reasoning.add_insight("database is the main bottleneck")
    state.reasoning.update_facts("current_query_time", "500ms")

    # Build complete context
    user_context = state.get_situated_context()
    reasoning_context = state.reasoning.compress_for_context()

    # Verify user context
    assert "USER CONTEXT:" in user_context
    assert "technical and detailed" in user_context
    assert "optimize performance" in user_context
    assert "python" in user_context
    assert "high-performance service" in user_context

    # Verify reasoning context
    assert "GOAL: optimize database queries" in reasoning_context
    assert "STRATEGY: analyze bottlenecks then optimize" in reasoning_context
    assert "INSIGHTS: database is the main bottleneck" in reasoning_context
    assert "FACTS: current_query_time: 500ms" in reasoning_context

    # Combined context should provide comprehensive understanding
    combined_context = user_context + "\n" + reasoning_context
    assert len(combined_context) > 0
    assert "optimize" in combined_context.lower()
    assert "performance" in combined_context.lower()
