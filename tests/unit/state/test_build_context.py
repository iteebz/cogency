"""Context building tests - Comprehensive context assembly."""

from cogency.memory.compression import compress
from cogency.state import AgentState
from cogency.state.context import execution_history, knowledge_synthesis, readiness_assessment
from cogency.state.reasoning import Reasoning
from cogency.state.user import UserProfile
from cogency.tools.shell import Shell


def test_contextcompression():
    """Test reasoning context compression for LLM context."""
    context = Reasoning(goal="test goal", strategy="test strategy")
    context.learn("key insight")
    context.update_facts("important_fact", "fact_value")
    context.record_thinking("complex analysis", [{"tool": "test"}])

    compressed = context.compress_for_context()

    assert "GOAL: test goal" in compressed
    assert "STRATEGY: test strategy" in compressed
    assert "FACTS: important_fact: fact_value" in compressed
    assert "INSIGHTS: key insight" in compressed
    assert "LAST THINKING: complex analysis" in compressed


def test_profile_injection():
    """Test user profile context for agent initialization."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "technical"
    profile.goals = ["complete project", "learn skills"]
    profile.expertise = ["python", "ml"]
    profile.projects = {"current": "test project"}

    context = compress(profile)

    assert "COMMUNICATION: technical" in context
    assert "CURRENT GOALS:" in context
    assert "EXPERTISE: python, ml" in context
    assert "ACTIVE PROJECTS: current: test project" in context


def test_situated_context():
    """Test AgentState situated context building."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "concise"
    profile.goals = ["efficiency"]

    state = AgentState(query="test query", user_profile=profile)

    situated_context = state.get_situated_context()

    assert situated_context.startswith("USER CONTEXT:")
    assert "COMMUNICATION: concise" in situated_context
    assert "CURRENT GOALS: efficiency" in situated_context


def test_context_building():
    """Test building comprehensive context from all components."""
    # Create user profile with rich context
    profile = UserProfile(user_id="expert_user")
    profile.communication_style = "technical and detailed"
    profile.goals = ["optimize performance", "maintain code quality"]
    profile.expertise = ["python", "distributed systems", "optimization"]
    profile.projects = {"current": "high-performance service"}
    profile.preferences = {"format": "structured", "detail_level": "high"}

    # Create agent state
    state = AgentState(query="optimize database queries", user_profile=profile)

    # Add reasoning context
    state.reasoning.strategy = "analyze bottlenecks then optimize"
    state.reasoning.learn("database is the main bottleneck")
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


def test_execution_history_empty():
    """Test execution history with no completed calls."""
    state = AgentState("test query")
    tools = [Shell()]

    history = execution_history(state, tools)

    assert history == ""


def test_execution_history_success():
    """Test execution history with successful tool calls."""
    state = AgentState("test query")
    tools = [Shell()]

    # Mock successful shell execution
    state.execution.completed_calls = [
        {
            "name": "shell",
            "args": {"command": "echo hello"},
            "success": True,
            "data": {"stdout": "hello\n", "stderr": "", "returncode": 0},
            "error": None,
        }
    ]

    history = execution_history(state, tools)

    assert "EXECUTION HISTORY:" in history
    assert "✓ shell({'command': 'echo hello'})" in history
    assert "→" in history
    assert "hello" in history


def test_execution_history_failure():
    """Test execution history with failed tool calls."""
    state = AgentState("test query")
    tools = [Shell()]

    # Mock failed shell execution
    state.execution.completed_calls = [
        {
            "name": "shell",
            "args": {"command": "invalid_command"},
            "success": False,
            "data": None,
            "error": "Command not found",
        }
    ]

    history = execution_history(state, tools)

    assert "EXECUTION HISTORY:" in history
    assert "✗ shell({'command': 'invalid_command'})" in history
    assert "FAILED: Resource not found - verify path exists. Error: Command not found" in history


def test_execution_history_mixed():
    """Test execution history with mixed success/failure."""
    state = AgentState("test query")
    tools = [Shell()]

    state.execution.completed_calls = [
        {
            "name": "shell",
            "args": {"command": "echo hello"},
            "success": True,
            "data": {"stdout": "hello\n", "stderr": "", "returncode": 0},
            "error": None,
        },
        {
            "name": "shell",
            "args": {"command": "invalid_cmd"},
            "success": False,
            "data": None,
            "error": "Command not found",
        },
    ]

    history = execution_history(state, tools)

    assert "✓ shell({'command': 'echo hello'})" in history
    assert "✗ shell({'command': 'invalid_cmd'})" in history
    assert "FAILED: Resource not found - verify path exists. Error: Command not found" in history


def test_execution_history_truncation():
    """Test execution history limits to last 5 results."""
    state = AgentState("test query")
    tools = [Shell()]

    # Create 7 completed calls
    state.execution.completed_calls = [
        {
            "name": "shell",
            "args": {"command": f"echo {i}"},
            "success": True,
            "data": {"stdout": f"{i}\n", "stderr": "", "returncode": 0},
            "error": None,
        }
        for i in range(7)
    ]

    history = execution_history(state, tools)

    # Should only show last 5 (indices 2-6)
    assert "echo 0" not in history
    assert "echo 1" not in history
    assert "echo 2" in history
    assert "echo 6" in history
    lines = history.split("\n")
    execution_lines = [line for line in lines if line.startswith("✓")]
    assert len(execution_lines) == 5


def test_knowledge_synthesis_empty():
    """Test knowledge synthesis with no successful calls."""
    state = AgentState("test query")

    knowledge = knowledge_synthesis(state)

    assert knowledge == ""


def test_knowledge_synthesis_shell():
    """Test knowledge synthesis extracts shell output."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {
            "name": "shell",
            "success": True,
            "data": {"stdout": "test output", "stderr": "", "returncode": 0},
            "error": None,
        }
    ]

    knowledge = knowledge_synthesis(state)

    assert "KNOWLEDGE GATHERED:" in knowledge
    assert "Command output: test output" in knowledge


def test_knowledge_synthesis_files():
    """Test knowledge synthesis extracts file content info."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {"name": "files", "success": True, "data": "file content here", "error": None}
    ]

    knowledge = knowledge_synthesis(state)

    assert "KNOWLEDGE GATHERED:" in knowledge
    assert "File content: 17 chars loaded" in knowledge


def test_knowledge_synthesis_search():
    """Test knowledge synthesis extracts search results count."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {
            "name": "search",
            "success": True,
            "data": [{"title": "result1"}, {"title": "result2"}],
            "error": None,
        }
    ]

    knowledge = knowledge_synthesis(state)

    assert "KNOWLEDGE GATHERED:" in knowledge
    assert "Found 2 search results" in knowledge


def test_knowledge_synthesis_mixed():
    """Test knowledge synthesis with multiple tool types."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {
            "name": "shell",
            "success": True,
            "data": {"stdout": "command output", "stderr": "", "returncode": 0},
            "error": None,
        },
        {"name": "files", "success": True, "data": "file content", "error": None},
        {"name": "search", "success": True, "data": [{"title": "result"}], "error": None},
    ]

    knowledge = knowledge_synthesis(state)

    assert "Command output: command output" in knowledge
    assert "File content: 12 chars loaded" in knowledge
    assert "Found 1 search results" in knowledge


def test_readiness_assessment_ready():
    """Test readiness assessment when ready to respond."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {
            "name": "shell",
            "success": True,
            "data": {"stdout": "success", "stderr": "", "returncode": 0},
            "error": None,
        }
    ]

    readiness = readiness_assessment(state)

    assert "RESPONSE READINESS:" in readiness
    assert "READY - Have successful results, no recent failures" in readiness


def test_readiness_assessment_recent_failures():
    """Test readiness assessment with recent failures."""
    state = AgentState("test query")

    # Add successful call earlier, then 2 recent failures (last 3 should have 2 failures)
    state.execution.completed_calls = [
        {
            "name": "shell",
            "success": True,
            "data": {"stdout": "old success", "stderr": "", "returncode": 0},
            "error": None,
        },
        {
            "name": "shell",
            "success": True,
            "data": {"stdout": "initial success", "stderr": "", "returncode": 0},
            "error": None,
        },
        {"name": "shell", "success": False, "data": None, "error": "error 1"},
        {"name": "shell", "success": False, "data": None, "error": "error 2"},
    ]

    readiness = readiness_assessment(state)

    assert "CONSIDER RESPONDING - Multiple recent failures" in readiness


def test_readiness_assessment_continue():
    """Test readiness assessment when should continue."""
    state = AgentState("test query")

    state.execution.completed_calls = [
        {"name": "shell", "success": False, "data": None, "error": "single failure"}
    ]

    readiness = readiness_assessment(state)

    assert "CONTINUE - Gathering more information" in readiness
