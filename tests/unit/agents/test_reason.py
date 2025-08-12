"""Tests for agent reasoning logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.agents.reason import _analyze_query, _build_context, _build_tool_registry, reason


@pytest.mark.asyncio
async def test_reason_direct_response():
    """Test reason returning direct response."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.query = "What is 2+2?"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.agents.reason._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "Simple math question",
                "response": "4",
                "actions": [],
            }

            result = await reason(mock_state, mock_llm, tools)

            assert result["reasoning"] == "Simple math question"
            assert result["response"] == "4"
            assert result["actions"] == []

            # Check state was updated
            assert mock_state.execution.iteration == 1
            assert len(mock_state.workspace.thoughts) == 1


@pytest.mark.asyncio
async def test_reason_with_actions():
    """Test reason returning actions for execution."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.query = "Create a file"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = [Mock()]

    with patch("cogency.agents.reason._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "Need to create file",
                "response": None,
                "actions": [{"name": "files", "args": {"operation": "create"}}],
            }

            result = await reason(mock_state, mock_llm, tools)

            assert result["reasoning"] == "Need to create file"
            assert result["response"] is None
            assert len(result["actions"]) == 1
            assert result["actions"][0]["name"] == "files"

            # Check actions were stored in state
            assert mock_state.execution.pending_calls == result["actions"]


@pytest.mark.asyncio
async def test_reason_max_iterations_reached():
    """Test reason force completion at max iterations."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 9  # At max - 1
    mock_state.execution.max_iterations = 10
    mock_state.execution.completed_calls = [
        {"tool": "test_tool", "result": {"result": "test output"}}
    ]
    mock_state.query = "Test query"

    tools = []

    with patch("cogency.events.emit") as mock_emit:
        result = await reason(mock_state, mock_llm, tools)

        assert mock_state.execution.iteration == 10  # Incremented
        assert "maximum iterations" in result["reasoning"]
        assert "Task completed after 10 iterations" in result["response"]
        assert result["actions"] == []

        # Check force completion event
        force_calls = [
            call
            for call in mock_emit.call_args_list
            if len(call[1]) > 0 and call[1].get("state") == "force_completion"
        ]
        assert len(force_calls) >= 1


@pytest.mark.asyncio
async def test_reason_max_iterations_no_completed_calls():
    """Test reason force completion with no completed calls."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 9
    mock_state.execution.max_iterations = 10
    mock_state.execution.completed_calls = []  # No completed work
    mock_state.query = "Test query"

    tools = []

    result = await reason(mock_state, mock_llm, tools)

    assert "Task processed through 10 iterations" in result["response"]


@pytest.mark.asyncio
async def test_reason_no_actions_fallback():
    """Test reason fallback when no actions provided."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.query = "Test query"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.agents.reason._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "No specific actions needed",
                "response": None,
                "actions": [],  # Empty actions
            }

            result = await reason(mock_state, mock_llm, tools)

            assert "No specific actions" in result["reasoning"]
            assert "I don't have specific actions to take" in result["response"]
            assert result["actions"] == []


@pytest.mark.asyncio
async def test_reason_error_handling():
    """Test reason error handling."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0

    tools = []

    # Mock _analyze_query to raise exception
    with patch("cogency.agents.reason._analyze_query", side_effect=Exception("Analysis failed")):
        with patch("cogency.events.emit") as mock_emit:
            result = await reason(mock_state, mock_llm, tools)

            assert "Error during reasoning" in result["reasoning"]
            assert "I encountered an error while reasoning" in result["response"]
            assert result["actions"] == []

            # Check error event was emitted
            error_calls = [
                call
                for call in mock_emit.call_args_list
                if len(call[1]) > 0 and call[1].get("state") == "error"
            ]
            assert len(error_calls) >= 1


@pytest.mark.asyncio
async def test_analyze_query_success():
    """Test _analyze_query parsing successful LLM response."""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = '{"reasoning": "test", "response": "answer", "actions": []}'

    with patch("cogency.events.emit"):
        result = await _analyze_query(mock_llm, "test query", "tools", "context", 1, 10)

        assert result["reasoning"] == "test"
        assert result["response"] == "answer"
        assert result["actions"] == []

        # Check LLM was called with proper prompt
        mock_llm.generate.assert_called_once()
        messages = mock_llm.generate.call_args[0][0]
        assert len(messages) == 1
        assert "test query" in messages[0]["content"]


@pytest.mark.asyncio
async def test_analyze_query_json_extraction():
    """Test _analyze_query extracting JSON from mixed response."""
    mock_llm = AsyncMock()
    # LLM returns text with embedded JSON
    mock_llm.generate.return_value = 'Here is my analysis:\n{"reasoning": "extracted", "response": null, "actions": [{"name": "test"}]}\nEnd of response.'

    result = await _analyze_query(mock_llm, "test", "tools", "context", 1, 10)

    assert result["reasoning"] == "extracted"
    assert result["response"] is None
    assert len(result["actions"]) == 1
    assert result["actions"][0]["name"] == "test"


@pytest.mark.asyncio
async def test_analyze_query_json_error():
    """Test _analyze_query handling JSON parse errors."""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Invalid JSON response that cannot be parsed"

    with patch("cogency.events.emit") as mock_emit:
        result = await _analyze_query(mock_llm, "test", "tools", "context", 1, 10)

        assert "Analysis parsing failed" in result["reasoning"]
        assert "Could you rephrase your request" in result["response"]
        assert result["actions"] == []

        # Check JSON error event
        json_error_calls = [
            call
            for call in mock_emit.call_args_list
            if len(call[1]) > 0 and call[1].get("state") == "json_error"
        ]
        assert len(json_error_calls) >= 1


def test_build_context():
    """Test _build_context delegates to state."""
    mock_state = Mock()
    mock_state.context.return_value = "test context string"

    result = _build_context(mock_state)

    assert result == "test context string"
    mock_state.context.assert_called_once()


def test_build_tool_registry_empty():
    """Test _build_tool_registry with empty tools."""
    result = _build_tool_registry([])
    assert result == "No tools available."

    result = _build_tool_registry(None)
    assert result == "No tools available."


def test_build_tool_registry_with_tools():
    """Test _build_tool_registry with tool instances."""
    # Mock tool with all attributes
    tool1 = Mock()
    tool1.name = "test_tool"
    tool1.description = "Test tool description"
    tool1.schema = "test_tool(arg='value')"
    tool1.examples = ["test_tool(arg='example')"]
    tool1.rules = ["Use carefully", "Check inputs"]

    # Mock tool with minimal attributes
    tool2 = Mock()
    tool2.name = "simple_tool"
    tool2.description = "Simple tool"
    tool2.schema = "simple_tool()"
    tool2.examples = []
    tool2.rules = []

    tools = [tool1, tool2]
    result = _build_tool_registry(tools)

    # Check both tools are included
    assert "- test_tool: Test tool description" in result
    assert "- simple_tool: Simple tool" in result

    # Check schema is included
    assert "Schema: test_tool(arg='value')" in result
    assert "Schema: simple_tool()" in result

    # Check examples and rules for tool1
    assert "Example: test_tool(arg='example')" in result
    assert "Rule: Use carefully" in result
    assert "Rule: Check inputs" in result


def test_build_tool_registry_missing_attributes():
    """Test _build_tool_registry with tools missing optional attributes."""
    tool = Mock()
    tool.name = "minimal_tool"
    tool.description = "Minimal tool"
    # Missing schema, examples, rules attributes

    result = _build_tool_registry([tool])

    assert "- minimal_tool: Minimal tool" in result
    assert "Schema: No schema" in result  # Fallback for missing schema


@pytest.mark.asyncio
async def test_reason_workspace_thoughts_update():
    """Test reason updates workspace thoughts correctly."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.query = "Test query"
    mock_state.context.return_value = "context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01T10:00:00"

    tools = []

    with patch("cogency.agents.reason._analyze_query") as mock_analyze:
        mock_analyze.return_value = {
            "reasoning": "Detailed reasoning process",
            "response": "Final answer",
            "actions": [],
        }

        await reason(mock_state, mock_llm, tools)

        # Check thought was added to workspace
        assert len(mock_state.workspace.thoughts) == 1
        thought = mock_state.workspace.thoughts[0]
        assert thought["iteration"] == 1  # After increment
        assert thought["reasoning"] == "Detailed reasoning process"
        assert thought["timestamp"] == "2024-01-01T10:00:00"
