"""MCP Server implementation for Cogency Agent - Clean MCP standards-compliant implementation"""

from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.websocket import websocket_server
from mcp.shared.exceptions import ErrorData, McpError
from mcp.types import TextContent, Tool
from pydantic import BaseModel


class InteractionRequest(BaseModel):
    """Request for agent interaction from UI component"""

    input_text: str
    context: Dict[str, Any] = {}


class MCPServer:
    """MCP Server for Cogency Agent communication"""

    def __init__(self, agent):
        self.agent = agent
        self.server = Server("cogency")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP tool handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="agent_interact",
                    description="Interact with the Cogency agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input_text": {
                                "type": "string",
                                "description": "Input text to send to the agent",
                            },
                            "context": {
                                "type": "object",
                                "description": "Optional context information",
                            },
                        },
                        "required": ["input_text"],
                    },
                ),
                Tool(
                    name="agent_query",
                    description="Query the agent with specific context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query to send to the agent",
                            },
                            "context": {
                                "type": "object",
                                "description": "Context for the query",
                            },
                        },
                        "required": ["query"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool"""
            if name == "agent_interact":
                return await self._interact(arguments)
            elif name == "agent_query":
                return await self._query(arguments)
            else:
                raise McpError(ErrorData(code=404, message=f"Unknown tool: {name}"))

    async def _interact(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle agent interaction"""
        input_text = arguments.get("input_text", "")
        context = arguments.get("context", {})

        try:
            # Process through the agent
            response = await self.agent.process(input_text, context)
            return [TextContent(type="text", text=response)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _query(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle agent query"""
        query = arguments.get("query", "")
        context = arguments.get("context", {})

        try:
            # Process through the agent
            response = await self.agent.process(query, context)
            return [TextContent(type="text", text=response)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def serve_stdio(self) -> None:
        """Serve MCP over stdio"""
        async with stdio_server(self.server) as streams:
            await self.server.run(
                streams[0], streams[1], self.server.create_initialization_options()
            )

    async def serve_websocket(self, host: str = "localhost", port: int = 8765) -> None:
        """Serve MCP over websocket"""
        await websocket_server(self.server, host, port)


def setup_mcp(agent, enabled: bool) -> Optional[MCPServer]:
    """Setup MCP server if enabled and available."""
    if not enabled:
        return None
    try:
        return MCPServer(agent)
    except ImportError:
        raise ImportError("Install cogency[mcp] for MCP support") from None


async def serve(
    mcp_server: MCPServer, transport: str = "stdio", host: str = "localhost", port: int = 8765
) -> None:
    """Start MCP server with specified transport type"""
    if not mcp_server:
        raise ValueError("MCP server not enabled. Set mcp=True in Agent constructor")
    if transport == "stdio":
        await mcp_server.serve_stdio()
    elif transport == "websocket":
        await mcp_server.serve_websocket(host, port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")
