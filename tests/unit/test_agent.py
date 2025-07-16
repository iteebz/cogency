import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from cogency.agent import Agent
from cogency.context import Context
from cogency.llm.mock import MockLLM
from cogency.memory.filesystem import FSMemory
from cogency.tools.base import BaseTool

@pytest.mark.asyncio
async def test_agent_init_defaults(mock_llm, fs_memory_fixture):
    """Agent initializes with default LLM, FSMemory, and auto-discovered tools."""
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    assert agent.name == "test_agent"
    assert agent.llm is mock_llm
    assert isinstance(agent.memory, FSMemory)
    assert agent.workflow is not None
    assert isinstance(agent.tools, list)
    # Check that some default tools are present (e.g., memory tools)
    assert any(tool.name == "memorize" for tool in agent.tools)
    assert any(tool.name == "recall" for tool in agent.tools)

@pytest.mark.asyncio
async def test_agent_init_custom_tools(mock_llm, mock_tool, fs_memory_fixture):
    """Agent initializes with provided custom tools in addition to default ones."""
    agent = Agent(name="test_agent", llm=mock_llm, tools=[mock_tool], memory=fs_memory_fixture)
    assert mock_tool in agent.tools
    assert any(tool.name == "memorize" for tool in agent.tools) # Default tools still present

@pytest.mark.asyncio
async def test_agent_stream_basic(mock_llm, fs_memory_fixture):
    """Agent stream yields chunks including final reasoning output."""
    mock_llm.response = "Final reasoning: This is the answer."
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    
    chunks = []
    async for chunk in agent.stream("test query"):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert any("📝 Final reasoning: This is the answer." in chunk for chunk in chunks)

@pytest.mark.asyncio
async def test_agent_run_basic(mock_llm, fs_memory_fixture):
    """Agent run returns the final response from the stream."""
    mock_llm.response = "The result is 42."
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    
    result = await agent.run("What is the result?")
    
    assert result == "The result is 42."

@pytest.mark.asyncio
async def test_agent_run_no_reasoning_output(mock_llm, fs_memory_fixture):
    """Agent run returns 'No response generated' if no reasoning output is found."""
    mock_llm.response = ""
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    
    result = await agent.run("Empty query")
    
    assert result == "No response generated"

@pytest.mark.asyncio
async def test_init_state(mock_llm, fs_memory_fixture):
    """_init_state correctly initializes agent state."""
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    query = "Initial query"
    
    state = agent._init_state(query)
    
    assert state["query"] == query
    assert "trace" in state
    assert "context" in state
    assert isinstance(state["context"], Context)
    assert state["context"].current_input == query

@pytest.mark.asyncio
async def test_init_state_with_existing_context(mock_llm, fs_memory_fixture):
    """_init_state updates existing context with new input."""
    agent = Agent(name="test_agent", llm=mock_llm, memory=fs_memory_fixture)
    initial_context = Context(current_input="old input")
    query = "new input"
    
    state = agent._init_state(query, context=initial_context)
    
    assert state["query"] == query
    assert state["context"] is initial_context # Should be the same object
    assert state["context"].current_input == query
