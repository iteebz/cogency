from typing import Any, AsyncIterator, Optional, Union, Literal

from cogency import decorators
from cogency.config import Robust, Observe, Persist
from cogency.state import State
from cogency.utils.auto import detect_llm
from cogency.utils.notify import Notifier
from cogency.phases.act import Act, Preprocess, Reason, Respond

MAX_QUERY_LENGTH = 10000

DEFAULT_SYSTEM_PROMPT = 'You are Cogency, an AI assistant with access to tools like code execution, file operations, web search, and more. Be honest about your capabilities. Be concise and direct unless detail is specifically requested.\n\nFor reasoning phases, output JSON: {"reasoning": "brief thought", "tool_calls": [{"name": "tool_name", "args": {...}}]}. Empty tool_calls array if no tools needed.\n\nFor final responses, be brief and helpful. Don\'t over-explain unless asked.'


class Agent:
    """Cognitive agent with streaming execution, tool integration, memory and adaptive reasoning"""

    def __init__(
        self,
        name: str = "cogency",
        *,  # Force keyword-only arguments
        # Backend Systems (things with constructors)
        llm: Optional[Any] = None,
        tools: Optional[Any] = None,
        memory: Optional[Any] = None,
        
        # Agent Personality
        prompt: Optional[str] = None,
        identity: Optional[str] = None,
        output_schema: Optional[Any] = None,
        
        # Execution Control
        mode: Literal["fast", "deep", "adapt"] = "adapt",
        depth: int = 10,
        
        # User Feedback
        notify: bool = True,
        debug: bool = False,
        
        # System Behaviors (@phase decorator control)
        robust: Union[bool, Robust] = True,
        observe: Union[bool, Observe] = False,
        persist: Union[bool, Persist] = False,
        
        # Integrations
        mcp: bool = False,
    ) -> None:
        self.name = name
        self.debug = debug
        self.notify = notify
        self.depth = depth
        
        # Mode handling
        self.deep = mode == "deep"
        self.adapt = mode == "adapt"

        # Configure @phase decorator behavior
        self.robust_config = robust if isinstance(robust, Robust) else Robust() if robust else None
        self.observe_config = observe if isinstance(observe, Observe) else Observe() if observe else None
        
        # Set up state persistence
        if persist:
            if isinstance(persist, Persist):
                self.persistence = persist
            else:
                self.persistence = Persist()
        else:
            self.persistence = None
            
        # Configure decorators with actual config objects - no ceremony
        decorators.configure_decorators(
            robust_config=self.robust_config,
            observe_config=self.observe_config,
            persistence_manager=self.persistence
        )

        # Backend auto-detection and setup
        self.llm = llm or detect_llm()
        
        # Setup memory - default enabled
        if memory is None:
            from cogency.memory.backends.filesystem import FileBackend
            self.memory = FileBackend(".cogency/memory")
        elif memory is False:
            self.memory = None
        else:
            self.memory = memory
            
        # Setup tools - auto-discover if not provided
        if tools is None:
            from cogency.tools.registry import ToolRegistry
            self.tools = ToolRegistry.get_tools(memory=self.memory)
        else:
            self.tools = tools
            
        # Add recall tool if memory enabled
        if self.memory:
            from cogency.tools.recall import Recall
            if not any(isinstance(tool, Recall) for tool in self.tools):
                self.tools.append(Recall(self.memory))
        
        # Agent personality
        self.system_prompt = prompt or DEFAULT_SYSTEM_PROMPT
        self.identity = identity or ""
        self.json_schema = output_schema
        
        # State management
        self.user_states: dict[str, State] = {}
        self.last_state: Optional[dict] = None  # Store for traces()

        # Create phase instances with injected dependencies - zero ceremony


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
        if mcp:
            try:
                from cogency.mcp.server import MCPServer
                self.mcp_server: Optional[Any] = MCPServer(self)
            except ImportError as e:
                raise ImportError("MCP package required for mcp=True") from e
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
            self.depth,
            self.user_states,
            self.persistence,
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
            trace=self.debug,
            verbose=self.notify,
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
                self.depth,
                self.user_states,
                self.persistence,
                self.llm,
            )
            state.notify = self.notify
            state.debug = self.debug

            # Apply deep mode and adapt overrides
            if self.deep:
                state.react_mode = "deep"
            # Note: adapt flag will be used in reason phase to disable mode switching

            # Set up trace callback for non-streaming mode
            if self.debug:
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
            raise ValueError("MCP server not enabled. Set mcp=True in Agent constructor")
        if transport == "stdio":
            async with self.mcp_server.serve_stdio():
                pass
        elif transport == "websocket":
            await self.mcp_server.serve_websocket(host, port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")


__all__ = ["Agent", "State"]
