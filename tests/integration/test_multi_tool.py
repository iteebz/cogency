"""Integration test for multi-tool execution in ReAct flow."""

from unittest.mock import AsyncMock

import pytest

from cogency.core.react import react
from cogency.lib.result import Ok


@pytest.fixture
def mock_llm_multi_tool():
    """Mock LLM that executes tools then provides final response."""
    llm = AsyncMock()

    # First response: execute multiple tools
    first_response = """<thinking>
I need to write a file and then search for information. I'll use multiple tools.
</thinking>

<tools>
[
    {"name": "file_write", "args": {"filename": "notes.txt", "content": "Research notes"}},
    {"name": "search", "args": {"query": "Python async best practices"}}
]
</tools>

<response></response>"""

    # Second response: final answer after tools executed
    second_response = """<thinking>
Both tools have executed successfully. I can now provide the final response.
</thinking>

<tools>[]</tools>

<response>
Both tasks completed successfully. I've written your notes and searched for Python async best practices.
</response>"""

    # Mock multiple LLM calls for iterations
    llm.generate.side_effect = [Ok(first_response), Ok(second_response)]

    # Ensure no stream attribute to force batch processing
    if hasattr(llm, "stream"):
        delattr(llm, "stream")

    return llm


@pytest.fixture
def mock_multi_tools():
    """Mock multiple tools for testing."""
    file_write = AsyncMock()
    file_write.name = "file_write"
    file_write.execute.return_value = Ok("File written successfully")

    search = AsyncMock()
    search.name = "search"
    search.execute.return_value = Ok("Found 10 results about Python async")

    return {
        "file_write": file_write,
        "search": search,
    }


@pytest.mark.asyncio
async def test_multi_execution(mock_llm_multi_tool, mock_multi_tools):
    """Multi-tool execution."""
    result = await react(
        mock_llm_multi_tool, mock_multi_tools, "Take notes and research async", "user123"
    )

    assert result["type"] == "complete"
    assert "Both tasks completed successfully" in result["answer"]

    # Verify both tools were executed
    mock_multi_tools["file_write"].execute.assert_called_once_with(
        filename="notes.txt", content="Research notes"
    )
    mock_multi_tools["search"].execute.assert_called_once_with(query="Python async best practices")
