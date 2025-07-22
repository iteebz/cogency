import asyncio
from typing import Any, AsyncIterator, Optional

from cogency.context import Context
from cogency.flow import Flow
from cogency.llm import detect_llm
from cogency.memory.backends.filesystem import FileBackend
from cogency.output import Output
from cogency.state import State
from cogency.tools.registry import ToolRegistry


class Agent:
    """Cognitive agent with streaming execution, tool integration, memory and adaptive reasoning"""

    def __init__(self, name: str, trace: bool = False, verbose: bool = True, **opts: Any) -> None:
        self.name = name
        self.trace = trace
        self.verbose = verbose

        # Handle memory flag - clean API for memory control
        memory_enabled = opts.get("memory", True)  # Default: enabled
        if memory_enabled:
            # Memory enabled: create backend and add Recall tool
            memory_backend = opts.get("memory_backend") or FileBackend(
                opts.get("memory_dir", ".cogency/memory")
            )
        else:
            # Memory disabled: no backend, no recall
            memory_backend = None

        # Handle tools - only accept instances, not classes
        tools = opts.get("tools")
        if tools is not None:
            # Validate that all tools are instances, not classes
            for tool in tools:
                if isinstance(tool, type):
                    raise ValueError(
                        f"Tool {tool.__name__} must be instantiated. "
                        f"Use {tool.__name__}() instead of {tool.__name__}"
                    )
        else:
            # Auto-discover all registered tools
            tools = ToolRegistry.get_tools(memory=memory_backend)

        # Add Recall tool if memory is enabled and not already in tools
        if memory_enabled and memory_backend:
            from cogency.tools.recall import Recall

            # Check if Recall is already in tools
            has_recall = any(isinstance(tool, Recall) for tool in tools)
            if not has_recall:
                tools.append(Recall(memory_backend))

        # Get LLM (already @safe protected)
        llm = opts.get("llm") or detect_llm()

        self.flow = Flow(
            llm=llm,
            tools=tools,
            memory=memory_backend,
            system_prompt=opts.get("system_prompt")
            or f"You are {opts.get('identity', 'a helpful AI assistant')}.",
            identity=opts.get("identity"),
            json_schema=opts.get("json_schema"),
        )
        self.contexts: dict[str, Context] = {}
        self.last_output_manager: Optional[Output] = None  # Store for traces()

        # MCP server setup if enabled
        if opts.get("enable_mcp"):
            try:
                from cogency.mcp.server import MCPServer

                self.mcp_server: Optional[Any] = MCPServer(self)
            except ImportError as e:
                raise ImportError("MCP package required for enable_mcp=True") from e
        else:
            self.mcp_server: Optional[Any] = None

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution with input validation and security checks"""
        # Input validation - basic sanitization
        if not query or not query.strip():
            yield "⚠️ Empty query not allowed\n"
            return

        if len(query) > 10000:  # Reasonable limit
            yield "⚠️ Query too long (max 10,000 characters)\n"
            return

        # Basic prompt injection detection
        suspicious_patterns = [
            "ignore previous",
            "forget",
            "system:",
            "assistant:",
            "<s>",
            "</s>",
            "\n\nHuman:",
            "\n\nAssistant:",
        ]
        if any(pattern in query.lower() for pattern in suspicious_patterns):
            yield "⚠️ Suspicious input detected\n"
            return

        # Get or create context
        context = self.contexts.get(user_id) or Context(query, user_id=user_id)
        context.query = query
        context.add_message("user", query)  # Add user query to message history
        self.contexts[user_id] = context

        # Create streaming callback
        message_queue: asyncio.Queue[str] = asyncio.Queue()

        async def stream_cb(message: str) -> None:
            """Queue messages for streaming."""
            await message_queue.put(message)

        # Create Output with clean flags
        output_manager = Output(trace=self.trace, verbose=self.verbose, callback=stream_cb)

        # Store for traces()
        self.last_output_manager = output_manager

        # Clean state - zero ceremony
        state = State(context=context, query=query, output=output_manager)

        # Start execution in background
        output_manager.callback = stream_cb
        execution_task = asyncio.create_task(self.flow.flow.ainvoke(state))

        # Stream messages as they come
        try:
            while not execution_task.done():
                try:
                    message = await asyncio.wait_for(message_queue.get(), timeout=0.1)
                    yield message
                except asyncio.TimeoutError:
                    continue

            # Get any remaining messages
            while not message_queue.empty():
                yield message_queue.get_nowait()

        finally:
            await execution_task

    async def run(self, query: str, user_id: str = "default") -> str:
        """Run agent and return complete response as string"""
        chunks = []
        async for chunk in self.stream(query, user_id):
            if "🤖 " in chunk:
                chunks.append(chunk.split("🤖 ", 1)[1])
        return "".join(chunks).strip() or "No response generated"

    def traces(self) -> list[dict[str, Any]]:
        """Get traces from last execution for debugging"""
        if self.last_output_manager:
            return self.last_output_manager.traces()
        return []

    # MCP compatibility methods
    async def process(self, input_text: str, context: Optional[Context] = None) -> str:
        """Process input text with optional context for MCP compatibility"""
        return await self.run(input_text, context.user_id if context else "default")

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
