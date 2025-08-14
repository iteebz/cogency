"""Tests for agent reasoning logic."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from cogency.context.assembly import build_context
from cogency.reason.analyze import _analyze_query, reason
from cogency.tools.registry import build_tool_schemas


@pytest.mark.asyncio
async def test_reason_direct_response():
    """Test reason returning direct response."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10
    mock_state.execution.max_iterations = 10
    mock_state.query = "What is 2+2?"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.reason.analyze._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "Simple math question",
                "response": "4",
                "actions": [],
            }

            result = await reason(
                context="test context",
                execution=mock_state.execution,
                query=mock_state.query,
                user_id="test_user",
                llm=mock_llm,
                tools=tools,
            )
            result_data = result.unwrap()

            assert result_data["reasoning"] == "Simple math question"
            assert result_data["response"] == "4"
            assert result_data["actions"] == []

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
    mock_state.execution.max_iterations = 10
    mock_state.query = "Create a file"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    # Properly configured mock tool
    mock_tool = Mock()
    mock_tool.name = "files"
    mock_tool.description = "File operations tool"
    mock_tool.examples = []
    mock_tool.rules = []
    tools = [mock_tool]

    with patch("cogency.reason.analyze._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "Need to create file",
                "response": None,
                "actions": [{"name": "files", "args": {"operation": "create"}}],
            }

            result = await reason(
                context="test context",
                execution=mock_state.execution,
                query=mock_state.query,
                user_id="test_user",
                llm=mock_llm,
                tools=tools,
            )
            result_data = result.unwrap()

            assert result_data["reasoning"] == "Need to create file"
            assert result_data["response"] is None
            assert len(result_data["actions"]) == 1
            assert result_data["actions"][0]["name"] == "files"

            # Check actions were stored in state
            assert mock_state.execution.pending_calls == result_data["actions"]


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
        result = await reason(
            context="test context",
            execution=mock_state.execution,
            query=mock_state.query,
            user_id="test_user",
            llm=mock_llm,
            tools=tools,
        )
        result_data = result.unwrap()

        assert mock_state.execution.iteration == 10  # Incremented
        assert "maximum iterations" in result_data["reasoning"]
        assert "Task completed after 10 iterations" in result_data["response"]
        assert result_data["actions"] == []

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
    result_data = result.unwrap()

    assert "Task processed through 10 iterations" in result_data["response"]


@pytest.mark.asyncio
async def test_reason_no_actions_fallback():
    """Test reason fallback when no actions provided."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10
    mock_state.query = "Test query"
    mock_state.context.return_value = "test context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.reason.analyze._analyze_query") as mock_analyze:
        with patch("cogency.events.emit"):
            mock_analyze.return_value = {
                "reasoning": "No specific actions needed",
                "response": None,
                "actions": [],  # Empty actions
            }

            result = await reason(
                context="test context",
                execution=mock_state.execution,
                query=mock_state.query,
                user_id="test_user",
                llm=mock_llm,
                tools=tools,
            )
            result_data = result.unwrap()

            assert "No specific actions" in result_data["reasoning"]
            assert "I don't have specific actions to take" in result_data["response"]
            assert result_data["actions"] == []


@pytest.mark.asyncio
async def test_reason_error_handling():
    """Test reason error handling."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10

    tools = []

    # Mock _analyze_query to raise exception
    with patch("cogency.reason.analyze._analyze_query", side_effect=Exception("Analysis failed")):
        with patch("cogency.events.emit") as mock_emit:
            result = await reason(
                context="test context",
                execution=mock_state.execution,
                query=mock_state.query,
                user_id="test_user",
                llm=mock_llm,
                tools=tools,
            )
            result_data = result.unwrap()

            assert "Error during reasoning" in result_data["reasoning"]
            assert "I encountered an error while reasoning" in result_data["response"]
            assert result_data["actions"] == []

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
    from resilient_result import Result

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = Result.ok(
        '{"assessment": "test assessment", "approach": "test approach", "response": "answer", "actions": []}'
    )

    # Create mock state with messages() method
    mock_state = MagicMock()
    mock_state.messages.return_value = []

    with patch("cogency.events.emit"):
        result = await _analyze_query(mock_llm, mock_state, "test query", "tools", "context", 1, 10)

        assert result["assessment"] == "test assessment"
        assert result["approach"] == "test approach"
        assert result["response"] == "answer"
        assert result["actions"] == []

        # Check LLM was called with proper prompt structure (system + user)
        mock_llm.generate.assert_called_once()
        messages = mock_llm.generate.call_args[0][0]
        assert len(messages) == 2  # System message + user query
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "test query"
        # The query should be in the user message, not system message
        assert "test query" in messages[1]["content"]


@pytest.mark.asyncio
async def test_analyze_query_json_extraction():
    """Test _analyze_query extracting JSON from mixed response."""
    from resilient_result import Result

    mock_llm = AsyncMock()
    # LLM returns text with embedded JSON
    mock_llm.generate.return_value = Result.ok(
        'Here is my analysis:\n{"assessment": "extracted assessment", "approach": "extracted approach", "response": null, "actions": [{"name": "test"}]}\nEnd of response.'
    )

    # Create mock state with messages() method
    mock_state = MagicMock()
    mock_state.messages.return_value = []

    result = await _analyze_query(mock_llm, mock_state, "test", "tools", "context", 1, 10)

    assert result["assessment"] == "extracted assessment"
    assert result["approach"] == "extracted approach"
    assert result["response"] is None
    assert len(result["actions"]) == 1
    assert result["actions"][0]["name"] == "test"


@pytest.mark.asyncio
async def test_analyze_query_json_error():
    """Test _analyze_query handling JSON parse errors."""
    from resilient_result import Result

    mock_llm = AsyncMock()
    # First call returns invalid JSON, second call (correction) also fails
    mock_llm.generate.side_effect = [
        Result.ok("Invalid JSON response that cannot be parsed"),
        Result.ok("Still invalid JSON"),
    ]

    # Create mock state with messages() method
    mock_state = MagicMock()
    mock_state.messages.return_value = []

    with patch("cogency.events.emit") as mock_emit:
        result = await _analyze_query(mock_llm, mock_state, "test", "tools", "context", 1, 10)

        assert result["assessment"] == "JSON formatting failed, using natural language response"
        assert result["approach"] == "Direct response"
        assert result["response"] == "Invalid JSON response that cannot be parsed"
        assert result["actions"] == []

        # Check JSON error event
        json_error_calls = [
            call
            for call in mock_emit.call_args_list
            if len(call[1]) > 0 and call[1].get("state") == "json_error"
        ]
        assert len(json_error_calls) >= 1


async def test_build_context():
    """Test build_context from context.assembly."""
    # Test with minimal parameters
    result = await build_context()
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_tool_registry_empty():
    """Test build_tool_schemas with empty tools."""
    result = build_tool_schemas([])
    assert result == "no tools"

    result = build_tool_schemas([])
    assert result == "no tools"


def test_build_tool_registry_with_tools():
    """Test build_tool_schemas with tool instances."""
    # Mock tool with all attributes
    tool1 = Mock()
    tool1.name = "test_tool"
    tool1.description = "Test tool description"
    tool1.emoji = "🔧"
    tool1.examples = ["test_tool(arg='example')"]
    tool1.rules = ["Use carefully", "Check inputs"]

    # Mock tool with minimal attributes
    tool2 = Mock()
    tool2.name = "simple_tool"
    tool2.description = "Simple tool"
    tool2.emoji = "⚡"
    tool2.examples = []
    tool2.rules = []

    tools = [tool1, tool2]
    result = build_tool_schemas(tools)

    # Check both tools are included in the new format
    assert "[test_tool]" in result
    assert "Test tool description" in result
    assert "[simple_tool]" in result
    assert "Simple tool" in result

    # Check examples and rules for tool1
    assert "- test_tool(arg='example')" in result
    assert "- Use carefully" in result
    assert "- Check inputs" in result


def test_build_tool_registry_missing_attributes():
    """Test build_tool_schemas with tools missing optional attributes."""
    tool = Mock()
    tool.name = "minimal_tool"
    tool.description = "Minimal tool"
    tool.emoji = "📝"
    tool.examples = []
    tool.rules = []

    result = build_tool_schemas([tool])

    assert "[minimal_tool]" in result
    assert "Minimal tool" in result
    assert "Examples:\nNone" in result  # Fallback for empty examples
    assert "Rules:\nNone" in result  # Fallback for empty rules


@pytest.mark.asyncio
async def test_reason_workspace_thoughts_update():
    """Test reason updates workspace thoughts correctly."""
    mock_llm = AsyncMock()
    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10
    mock_state.query = "Test query"
    mock_state.context.return_value = "context"
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01T10:00:00"

    tools = []

    with patch("cogency.reason.analyze._analyze_query") as mock_analyze:
        mock_analyze.return_value = {
            "assessment": "Detailed assessment",
            "approach": "Detailed approach",
            "response": "Final answer",
            "actions": [],
        }

        await reason(mock_state, mock_llm, tools)

        # Check thought was added to workspace
        assert len(mock_state.workspace.thoughts) == 1
        thought = mock_state.workspace.thoughts[0]
        assert thought["iteration"] == 1  # After increment
        assert thought["assessment"] == "Detailed assessment"
        assert thought["approach"] == "Detailed approach"
        assert thought["timestamp"] == "2024-01-01T10:00:00"


@pytest.mark.asyncio
async def test_security_terminates_iteration_1():
    """Test security violation terminates on iteration 1."""
    from resilient_result import Result

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = Result.ok(
        '{"secure": false, "reasoning": "Security threat detected", "response": "Cannot assist with harmful request", "actions": []}'
    )

    mock_state = MagicMock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10
    mock_state.query = "rm -rf /"
    mock_state.context.return_value = "context"
    mock_state.messages.return_value = []
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.events.emit") as mock_emit:
        result = await reason(
            context="test context",
            execution=mock_state.execution,
            query=mock_state.query,
            user_id="test_user",
            llm=mock_llm,
            tools=tools,
        )
        result_data = result.unwrap()

        # Should terminate immediately with security response
        assert result_data["response"] == "Cannot assist with harmful request"
        assert result_data["actions"] == []
        assert "Security threat detected" in result_data["reasoning"]

        # Should only increment to iteration 1
        assert mock_state.execution.iteration == 1

        # Should emit security violation event
        security_calls = [
            call
            for call in mock_emit.call_args_list
            if len(call[1]) > 0 and call[1].get("state") == "security_violation"
        ]
        assert len(security_calls) == 1
        assert security_calls[0][1]["iteration"] == 1


@pytest.mark.asyncio
async def test_security_only_evaluated_iteration_1():
    """Test security context only added for iteration 1."""
    from resilient_result import Result

    mock_llm = AsyncMock()

    # First call (iteration 1) - should include security
    mock_llm.generate.return_value = Result.ok(
        '{"secure": true, "assessment": "Safe request assessment", "approach": "Safe approach", "response": null, "actions": [{"name": "test_tool", "args": {}}]}'
    )

    # Create mock state with messages() method
    mock_state = MagicMock()
    mock_state.messages.return_value = []

    with patch("cogency.events.emit"):
        # Iteration 1 - should include SECURITY_ASSESSMENT
        result = await _analyze_query(mock_llm, mock_state, "test query", "tools", "context", 1, 10)

        # Check the prompt includes security context
        call_args = mock_llm.generate.call_args[0][0][0]["content"]
        assert "SECURITY ASSESSMENT" in call_args
        assert "secure" in call_args
        assert result["assessment"] == "Safe request assessment"
        assert result["approach"] == "Safe approach"

        # Reset mock for iteration 2
        mock_llm.reset_mock()
        mock_llm.generate.return_value = Result.ok(
            '{"assessment": "Follow-up assessment", "approach": "Follow-up approach", "response": "Done", "actions": []}'
        )

        # Iteration 2 - should NOT include security context
        result = await _analyze_query(mock_llm, mock_state, "test query", "tools", "context", 2, 10)

        # Check the prompt does NOT include security context
        call_args = mock_llm.generate.call_args[0][0][0]["content"]
        assert "SECURITY ASSESSMENT" not in call_args
        # Note: "secure" will still appear in the JSON schema template, so we check for SECURITY_ASSESSMENT instead
        assert result["assessment"] == "Follow-up assessment"
        assert result["approach"] == "Follow-up approach"


@pytest.mark.asyncio
async def test_security_safe_request_continues():
    """Test safe request (secure: true) continues normal reasoning."""
    from resilient_result import Result

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = Result.ok(
        '{"secure": true, "assessment": "Safe math question assessment", "approach": "Direct calculation", "response": "4", "actions": []}'
    )

    mock_state = Mock()
    mock_state.execution = Mock()
    mock_state.execution.iteration = 0
    mock_state.execution.max_iterations = 10
    mock_state.query = "what is 2+2?"
    mock_state.user_id = "test_user"
    mock_state.context.return_value = "context"
    mock_state.messages.return_value = []
    mock_state.workspace = Mock()
    mock_state.workspace.thoughts = []
    mock_state.last_updated = "2024-01-01"

    tools = []

    with patch("cogency.events.emit") as mock_emit:
        with patch("cogency.context.assembly.build_context") as mock_build_context:
            mock_build_context.return_value = "test context"
            result = await reason(
                context="test context",
                execution=mock_state.execution,
                query=mock_state.query,
                user_id="test_user",
                llm=mock_llm,
                tools=tools,
            )
        result_data = result.unwrap()

        # Should process normally
        assert result_data["response"] == "4"
        assert result_data["assessment"] == "Safe math question assessment"
        assert result_data["approach"] == "Direct calculation"
        assert result_data["actions"] == []

        # Should increment iteration normally
        assert mock_state.execution.iteration == 1

        # Should NOT emit security violation
        security_calls = [
            call
            for call in mock_emit.call_args_list
            if len(call[1]) > 0 and call[1].get("state") == "security_violation"
        ]
        assert len(security_calls) == 0
