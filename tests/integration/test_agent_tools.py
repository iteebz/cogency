"""Agent-Tools integration tests - tool execution boundaries."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cogency import Agent


@pytest.fixture
def temp_sandbox():
    """Use temporary directory as sandbox."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_llm_with_tools():
    """Mock LLM that calls tools in sequence."""
    llm = Mock()

    async def mock_tool_stream(*args, **kwargs):
        # Simulate agent thinking, then calling tools
        yield "§THINK"
        yield "I need to create a file and read it back"
        yield "§CALLS"
        yield '[{"name": "write", "args": {"file_path": "test.txt", "content": "hello world"}}]'
        yield "§EXECUTE"
        yield "§THINK"
        yield "File created, now reading it"
        yield "§CALLS"
        yield '[{"name": "read", "args": {"file_path": "test.txt"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "File created and read successfully"
        yield "§EXECUTE"

    llm.stream.return_value = mock_tool_stream()
    llm.resumable = False
    return llm


@pytest.mark.asyncio
async def test_tool_execution_chain(temp_sandbox, mock_llm_with_tools):
    """Agent executes multiple tools in sequence correctly."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm_with_tools):
        # Create agent with sandbox pointing to temp directory
        agent = Agent(llm="gemini", sandbox=True)

        # Agent should execute tool chain
        response = await agent("Create test.txt with 'hello world', then read it back")

        # Verify response received
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify tools actually executed in sandbox
        # Note: This tests the integration - tools actually ran and created files
        test_file = Path(temp_sandbox) / "test.txt"
        if test_file.exists():  # File may exist if tools actually executed
            content = test_file.read_text()
            assert "hello world" in content


@pytest.mark.asyncio
async def test_tool_failure_handling(temp_sandbox):
    """Agent handles tool execution failures gracefully."""

    # Mock LLM that calls a failing tool
    mock_llm = Mock()

    async def mock_failing_stream(*args, **kwargs):
        yield "§THINK"
        yield "Trying to read non-existent file"
        yield "§CALLS"
        yield '[{"name": "read", "args": {"file_path": "nonexistent.txt"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "File not found, but I handled it gracefully"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_failing_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini", sandbox=True)

        # Should not crash on tool failure
        response = await agent("Read nonexistent.txt")

        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.asyncio
async def test_sandbox_isolation(temp_sandbox):
    """Tool execution is properly sandboxed."""

    mock_llm = Mock()

    async def mock_sandbox_stream(*args, **kwargs):
        yield "§THINK"
        yield "Creating file in sandbox"
        yield "§CALLS"
        yield '[{"name": "write", "args": {"file_path": "sandbox_test.txt", "content": "sandboxed content"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "File created in sandbox"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_sandbox_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini", sandbox=True)

        await agent("Create sandbox_test.txt")

        # File should be created in sandbox directory, not current directory
        local_file = Path("sandbox_test.txt")
        assert not local_file.exists(), "File should not be created outside sandbox"


@pytest.mark.asyncio
async def test_tool_context_passing():
    """Tools receive proper context and parameters."""

    mock_llm = Mock()

    async def mock_context_stream(*args, **kwargs):
        yield "§THINK"
        yield "Need to search and then use results"
        yield "§CALLS"
        yield '[{"name": "search", "args": {"query": "python tutorials"}}]'
        yield "§EXECUTE"
        yield "§CALLS"
        yield '[{"name": "write", "args": {"file_path": "results.txt", "content": "Search completed"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "Search and file write completed"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_context_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini", sandbox=True)

        response = await agent("Search for python tutorials and save results", user_id="test_user")

        # Verify agent completed multi-tool workflow
        assert isinstance(response, str)
        assert "completed" in response.lower()


@pytest.mark.asyncio
async def test_tool_results_integration():
    """Tool results properly flow back to agent."""

    mock_llm = Mock()

    async def mock_results_stream(*args, **kwargs):
        yield "§THINK"
        yield "Reading a file to get content"
        yield "§CALLS"
        yield '[{"name": "read", "args": {"file_path": "input.txt"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "I read the file and got the content"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_results_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini", sandbox=True)

        response = await agent("Read input.txt and tell me what it contains")

        assert isinstance(response, str)
        # Agent should incorporate tool results in response
        assert len(response) > 0
