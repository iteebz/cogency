"""State core functionality tests."""

from datetime import datetime

from cogency.state import Conversation, Execution, State, Workspace


def test_minimal_construction():
    state = State(query="test query")

    assert state.query == "test query"
    assert state.user_id == "default"
    assert state.task_id is not None
    assert isinstance(state.task_id, str)


def test_with_user_id():
    state = State(query="test query", user_id="custom_user")

    assert state.query == "test query"
    assert state.user_id == "custom_user"


def test_auto_initialization():
    state = State(query="test query")

    assert state.profile is not None
    assert state.conversation is not None
    assert state.workspace is not None
    assert state.execution is not None

    assert state.profile.user_id == "default"
    assert state.conversation.user_id == "default"
    assert state.workspace.objective == "test query"


def test_with_explicit_components():
    workspace = Workspace(objective="custom objective")
    conversation = Conversation(user_id="test_user")

    state = State(
        query="test query", user_id="test_user", workspace=workspace, conversation=conversation
    )

    assert state.workspace is workspace
    assert state.conversation is conversation
    assert state.workspace.objective == "custom objective"


def test_independence():
    state1 = State(query="query 1", user_id="user1")
    state2 = State(query="query 2", user_id="user2")

    state1.workspace.insights.append("insight 1")
    state1.execution.iteration = 5

    assert len(state2.workspace.insights) == 0
    assert state2.execution.iteration == 0
    assert state2.query == "query 2"
    assert state2.user_id == "user2"


def test_workspace_component():
    workspace = Workspace(objective="test objective")

    assert workspace.objective == "test objective"
    assert workspace.assessment == ""
    assert workspace.approach == ""
    assert isinstance(workspace.observations, list)
    assert isinstance(workspace.insights, list)
    assert isinstance(workspace.facts, dict)
    assert isinstance(workspace.thoughts, list)


def test_conversation_component():
    conversation = Conversation(user_id="test_user")

    assert conversation.user_id == "test_user"
    assert conversation.conversation_id is not None
    assert isinstance(conversation.messages, list)
    assert isinstance(conversation.last_updated, datetime)


def test_execution_component():
    execution = Execution()

    assert execution.iteration == 0
    assert execution.max_iterations == 10
    assert execution.stop_reason is None
    assert isinstance(execution.messages, list)
    assert execution.response is None
    assert isinstance(execution.pending_calls, list)
    assert isinstance(execution.completed_calls, list)
    assert execution.iterations_without_tools == 0
    assert isinstance(execution.tool_results, dict)


def test_component_isolation():
    state = State(query="test query")

    state.workspace.insights.append("workspace insight")
    state.conversation.messages.append({"role": "user", "content": "hello"})
    state.execution.iteration = 3

    assert len(state.workspace.insights) == 1
    assert len(state.conversation.messages) == 1
    assert state.execution.iteration == 3

    new_state = State(query="new query")
    assert len(new_state.workspace.insights) == 0
    assert len(new_state.conversation.messages) == 0
    assert new_state.execution.iteration == 0


def test_empty_context():
    state = State(query="test query")
    context = state.context()

    assert "Current objective: test query" in context


def test_context_with_insights():
    state = State(query="test query")
    state.workspace.insights = ["insight 1", "insight 2", "insight 3"]

    context = state.context()
    assert "Key insights:" in context
    assert "insight 2" in context
    assert "insight 3" in context


def test_context_with_tool_history():
    state = State(query="test query")
    state.execution.completed_calls = [
        {"tool": "search", "success": True, "result": {"result": "Found data"}},
        {"tool": "analyze", "success": False, "result": {"message": "Failed to analyze"}},
    ]

    context = state.context()
    assert "TOOL EXECUTION HISTORY:" in context
    assert "search: ✅ SUCCESS - Found data" in context
    assert "analyze: ❌ FAILED - Failed to analyze" in context


def test_messages():
    state = State(query="test query")

    messages = state.messages()
    assert isinstance(messages, list)
    assert len(messages) == 0

    state.conversation.messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]

    messages = state.messages()
    assert len(messages) == 2
    assert messages[0]["content"] == "hello"
    assert messages[1]["content"] == "hi"

    messages.append({"role": "user", "content": "test"})
    assert len(state.conversation.messages) == 2


def test_timestamps():
    state = State(query="test query")

    assert isinstance(state.created_at, datetime)
    assert isinstance(state.last_updated, datetime)


def test_task_id_uniqueness():
    state1 = State(query="query 1")
    state2 = State(query="query 2")

    assert state1.task_id != state2.task_id
    assert isinstance(state1.task_id, str)
    assert len(state1.task_id) > 10
