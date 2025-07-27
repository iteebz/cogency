"""MCP server tests - protocol and handler logic."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.mcp.server import InteractionRequest, MCPServer


@pytest.fixture
def mock_agent():
    agent = Mock()
    agent.process = AsyncMock(return_value="response")
    return agent


@pytest.fixture
def mcp_server(mock_agent):
    return MCPServer(mock_agent)


def test_init(mock_agent):
    server = MCPServer(mock_agent)
    assert server.agent is mock_agent
    assert server.server.name == "cogency"


def test_interaction_request():
    req = InteractionRequest(input_text="test", context={"key": "value"})
    assert req.input_text == "test"
    assert req.context == {"key": "value"}


def test_interaction_request_defaults():
    req = InteractionRequest(input_text="test")
    assert req.input_text == "test"
    assert req.context == {}


@pytest.mark.asyncio
async def test_interact_success(mcp_server, mock_agent):
    args = {"input_text": "hello", "context": {"test": True}}
    result = await mcp_server._interact(args)

    mock_agent.process.assert_called_once_with("hello", {"test": True})
    assert len(result) == 1
    assert result[0].type == "text"
    assert result[0].text == "response"


@pytest.mark.asyncio
async def test_interact_error(mcp_server, mock_agent):
    mock_agent.process.side_effect = Exception("test error")
    args = {"input_text": "hello"}
    result = await mcp_server._interact(args)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error: test error" in result[0].text


@pytest.mark.asyncio
async def test_query_success(mcp_server, mock_agent):
    args = {"query": "what?", "context": {"key": "val"}}
    result = await mcp_server._query(args)

    mock_agent.process.assert_called_once_with("what?", {"key": "val"})
    assert len(result) == 1
    assert result[0].type == "text"
    assert result[0].text == "response"


@pytest.mark.asyncio
async def test_query_error(mcp_server, mock_agent):
    mock_agent.process.side_effect = Exception("query error")
    args = {"query": "what?"}
    result = await mcp_server._query(args)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error: query error" in result[0].text
