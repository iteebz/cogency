from typing import Any, AsyncIterator, Optional

from cogency.context import Context
from cogency.flow import Flow
from cogency.identity import process_identity
from cogency.utils.auto import detect_llm
from cogency.state import State
from cogency.utils.notify import Notifier
from cogency.utils.setup import agent_services

MAX_QUERY_LENGTH = 10000

DEFAULT_SYSTEM_PROMPT = 'You are Cogency, an AI assistant with access to tools like code execution, file operations, web search, and more. Be honest about your capabilities. Be concise and direct unless detail is specifically requested.\n\nFor reasoning phases, output JSON: {"reasoning": "brief thought", "tool_calls": [{"name": "tool_name", "args": {...}}]}. Empty tool_calls array if no tools needed.\n\nFor final responses, be brief and helpful. Don\'t over-explain unless asked.'


class Agent:
    """Cognitive agent with streaming execution, tool integration, memory and adaptive reasoning"""

    def __init__(
        self,
        name: str = "cogency",
        *,  # Force keyword-only args
        llm: Optional[Any] = None,
        tools: Optional[Any] = None,
        memory: Any = True,
        memory_dir: str = ".cogency/memory",
        identity: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        trace: bool = False,
        verbose: bool = True,
        enable_mcp: bool = False,
        json_schema: Optional[Any] = None,
    ) -> None:
        self.name = name
        self.trace = trace
        self.verbose = verbose
        self.max_iterations = max_iterations

        # Setup tools and memory services
        agent_opts = {
            "tools": tools,
            "memory": memory,
            "memory_dir": memory_dir,
        }
        tools, memory = agent_services(agent_opts)

        # Get LLM (already @safe protected)
        llm = llm or detect_llm()

        self.flow = Flow(
            llm=llm,
            tools=tools,
            memory=memory,
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            identity=process_identity(identity),
            json_schema=json_schema,
        )
        self.contexts: dict[str, Context] = {}
        self.last_state: Optional[dict] = None  # Store for traces()

        # MCP server setup if enabled
        if enable_mcp:
            try:
                from cogency.mcp.server import MCPServer

                self.mcp_server: Optional[Any] = MCPServer(self)
            except ImportError as e:
                raise ImportError("MCP package required for enable_mcp=True") from e
        else:
            self.mcp_server: Optional[Any] = None

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution"""
        # Input validation
        if not query or not query.strip():
            yield "⚠️ Empty query not allowed\n"
            return

        if len(query) > MAX_QUERY_LENGTH:
            yield "⚠️ Query too long (max 10,000 characters)\n"
            return

        # Get or create context
        context = self.contexts.get(user_id) or Context(query, user_id=user_id)
        context.query = query
        context.add_message("user", query)  # Add user query to message history
        self.contexts[user_id] = context

        # Stream execution using Notifier
        notifier = Notifier(
            flow=self.flow,
            context=context,
            query=query,
            trace=self.trace,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
        )

        async for chunk in notifier.notify():
            yield chunk

        # Store state for traces()
        self.last_state = notifier.get_notifications()

    def run(self, query: str, user_id: str = "default") -> str:
        """Run agent and return complete response as string"""
        try:
            # Get or create context
            if user_id not in self.contexts:
                self.contexts[user_id] = Context(query)
            context = self.contexts[user_id]
            
            # Create state as dataclass with proper initialization
            from cogency.state import State
            state = State(
                context=context,
                query=query,
                verbose=True,
                trace=True,
            )
            
            # Use simple execution loop
            import asyncio
            from cogency.execution import run_agent
            
            # Build kwargs from flow attributes
            kwargs = {
                "llm": self.flow.llm,
                "tools": self.flow.tools,
                "system_prompt": self.flow.system_prompt,
                "identity": self.flow.identity,
                "json_schema": self.flow.json_schema,
                "memory": self.flow.memory,
            }
            
            result_state = asyncio.run(run_agent(state, **kwargs))
            self.last_state = result_state
            
            # Extract response from state
            response = getattr(result_state, 'response', None)
            return response or "No response generated"
            
        except Exception as e:
            # Make errors EXPLICIT
            import traceback
            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return f"ERROR: {e}"

    def traces(self) -> list[dict[str, Any]]:
        """Get traces from last execution for debugging"""
        if self.last_state:
            return self.last_state
        return []

    async def serve_mcp(
        self, transport: str = "stdio", host: str = "localhost", port: int = 8765
    ) -> None:
        """Start MCP server with specified transport type"""
        if not self.mcp_server:
            raise ValueError("MCP server not enabled. Set enable_mcp=True in Agent constructor")
        if transport == "stdio":
            async with self.mcp_server.serve_stdio():
                pass
        elif transport == "websocket":
            await self.mcp_server.serve_websocket(host, port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")


__all__ = ["Agent", "Context", "Flow", "State"]
