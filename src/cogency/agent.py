from typing import Any, AsyncIterator, Optional

from cogency import decorators
from cogency.state import State
from cogency.utils.auto import detect_llm
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
        robust: bool = True,
        observe: bool = False,
        persist: bool = False,
        persist_backend: Optional[Any] = None,
        deep: bool = False,
        adapt: bool = True,
    ) -> None:
        self.name = name
        self.trace = trace
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.deep = deep
        self.adapt = adapt

        # Set global robust and observe flags for decorators
        decorators._robust_enabled = robust
        decorators.set_observe_enabled(observe)

        # Set up state persistence
        if persist:
            from cogency.persistence import StateManager

            self.persistence_manager = StateManager(backend=persist_backend, enabled=True)
            decorators.set_persistence_manager(self.persistence_manager)
        else:
            self.persistence_manager = None

        # Setup tools and memory services
        agent_opts = {
            "tools": tools,
            "memory": memory,
            "memory_dir": memory_dir,
        }
        tools, memory = agent_services(agent_opts)

        # Store configuration directly
        self.llm = llm or detect_llm()
        self.tools = tools
        self.memory = memory
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.identity = identity or ""
        self.json_schema = json_schema
        self.user_states: dict[str, State] = {}
        self.last_state: Optional[dict] = None  # Store for traces()

        # Create phase instances with injected dependencies - zero ceremony
        from cogency.phases.act import Act
        from cogency.phases.preprocess import Preprocess
        from cogency.phases.reason import Reason
        from cogency.phases.respond import Respond

        self.preprocess_phase = Preprocess(
            llm=self.llm,
            tools=self.tools,
            memory=self.memory,
            system_prompt=self.system_prompt,
            identity=self.identity,
        )
        self.reason_phase = Reason(
            llm=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
            identity=self.identity,
            adapt=self.adapt,
        )
        self.act_phase = Act(tools=self.tools)
        self.respond_phase = Respond(
            llm=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
            identity=self.identity,
            json_schema=self.json_schema,
        )

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

        # Get or create state with persistence support
        from cogency.persistence import get_state

        state = await get_state(
            user_id,
            query,
            self.max_iterations,
            self.user_states,
            self.persistence_manager,
            self.llm,
        )

        state.add_message("user", query)

        # Stream execution using Notifier
        notifier = Notifier(
            state=state,
            llm=self.llm,
            tools=self.tools,
            memory=self.memory,
            system_prompt=self.system_prompt,
            identity=self.identity,
            json_schema=self.json_schema,
            trace=self.trace,
            verbose=self.verbose,
        )

        async for chunk in notifier.notify():
            yield chunk

        # Store state for traces()
        self.last_state = notifier.get_notifications()

    async def run(self, query: str, user_id: str = "default") -> str:
        """Run agent and return complete response as string (async)"""
        try:
            # Get or create state with persistence support
            from cogency.persistence import get_state

            state = await get_state(
                user_id,
                query,
                self.max_iterations,
                self.user_states,
                self.persistence_manager,
                self.llm,
            )
            state.verbose = self.verbose
            state.trace = self.trace

            # Apply deep mode and adapt overrides
            if self.deep:
                state.react_mode = "deep"
            # Note: adapt flag will be used in reason phase to disable mode switching

            # Set up trace callback for non-streaming mode
            if self.trace:
                state.callback = print

            # Use simple execution loop with zero ceremony
            from cogency.execution import run_agent

            # Phase instances already have dependencies injected
            await run_agent(
                state, self.preprocess_phase, self.reason_phase, self.act_phase, self.respond_phase
            )
            self.last_state = state

            # Extract response from state
            response = getattr(state, "response", None)
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


__all__ = ["Agent", "State"]
