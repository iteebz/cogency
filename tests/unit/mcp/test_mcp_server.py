import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.shared.exceptions import McpError
from mcp.types import TextContent, Tool
from mcp.shared.session import BaseSession
from mcp.shared.message import SessionMessage

from cogency.mcp.server import CogencyMCPServer

@pytest.fixture
def mock_agent():
    """Mock agent for testing CogencyMCPServer."""
    agent = MagicMock()
    agent.process_input = AsyncMock(return_value="Agent processed input")
    return agent

@pytest.fixture
def mock_mcp_server_class():
    """Mock the mcp.server.Server class."""
    with patch('cogency.core.mcp_server.Server') as MockServer:
        # Create mocks for the decorator calls
        mock_list_tools_decorator = MagicMock(side_effect=lambda func: func) # This mock will be called with the decorated function
        mock_call_tool_decorator = MagicMock(side_effect=lambda func: func) # This mock will be called with the decorated function

        # Configure the mock Server instance to return these decorator mocks
        MockServer.return_value.list_tools.return_value = mock_list_tools_decorator
        MockServer.return_value.call_tool.return_value = mock_call_tool_decorator
        
        yield MockServer

@pytest.fixture
def mcp_server(mock_agent, mock_mcp_server_class):
    """Fixture for CogencyMCPServer instance with mocked mcp.server.Server."""
    return CogencyMCPServer(mock_agent)

@pytest.mark.asyncio
async def test_list_tools(mcp_server, mock_mcp_server_class):
    """Test that list_tools returns the correct MCP tool definitions."""
    # Access the mock that was returned by the decorator call
    registered_list_tools_func = mock_mcp_server_class.return_value.list_tools.return_value.call_args[0][0]
    tools = await registered_list_tools_func()
    tool_names = [t.name for t in tools]

    assert "agent_interact" in tool_names
    assert "agent_query" in tool_names

    agent_interact_tool = next(t for t in tools if t.name == "agent_interact")
    assert agent_interact_tool.description == "Interact with the Cogency agent"
    assert "input_text" in agent_interact_tool.inputSchema["properties"]
    assert "context" in agent_interact_tool.inputSchema["properties"]
    assert "input_text" in agent_interact_tool.inputSchema["required"]

    agent_query_tool = next(t for t in tools if t.name == "agent_query")
    assert agent_query_tool.description == "Query the agent with specific context"
    assert "query" in agent_query_tool.inputSchema["properties"]
    assert "context" in agent_query_tool.inputSchema["properties"]
    assert "query" in agent_query_tool.inputSchema["required"]

@pytest.mark.asyncio
async def test_handle_agent_interact_success(mcp_server, mock_agent):
    """Test _handle_agent_interact successfully processes input."""
    arguments = {"input_text": "Hello", "context": {"user": "test"}}
    result = await mcp_server._handle_agent_interact(arguments)

    mock_agent.process_input.assert_called_once_with("Hello", {"user": "test"})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Agent processed input"

@pytest.mark.asyncio
async def test_handle_agent_interact_error(mcp_server, mock_agent):
    """Test _handle_agent_interact handles errors from agent.process_input."""
    mock_agent.process_input.side_effect = Exception("Agent error")
    arguments = {"input_text": "Error input"}
    result = await mcp_server._handle_agent_interact(arguments)

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Error: Agent error"

@pytest.mark.asyncio
async def test_handle_agent_query_success(mcp_server, mock_agent):
    """Test _handle_agent_query successfully processes query."""
    arguments = {"query": "What is the time?", "context": {"location": "NYC"}}
    result = await mcp_server._handle_agent_query(arguments)

    mock_agent.process_input.assert_called_once_with("What is the time?", {"location": "NYC"})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Agent processed input"

@pytest.mark.asyncio
async def test_handle_agent_query_error(mcp_server, mock_agent):
    """Test _handle_agent_query handles errors from agent.process_input."""
    mock_agent.process_input.side_effect = Exception("Query error")
    arguments = {"query": "Error query"}
    result = await mcp_server._handle_agent_query(arguments)

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Error: Query error"

@pytest.mark.asyncio
async def test_call_tool_unknown_tool(mcp_server, mock_mcp_server_class):
    """Test call_tool raises McpError for unknown tools."""
    registered_call_tool_func = mock_mcp_server_class.return_value.call_tool.return_value.call_args[0][0]
    
    with pytest.raises(McpError, match="Unknown tool: unknown_tool"):
        await registered_call_tool_func(name="unknown_tool", arguments={})