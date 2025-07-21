import asyncio
from typing import Optional, AsyncIterator, List, Dict, Any
from cogency.flow import Flow
from cogency.runner import StreamingRunner
from cogency.context import Context
from cogency.llm import auto_detect_llm
from cogency.tools.registry import ToolRegistry
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.state import AgentState
from cogency.output import OutputManager


def compose_system_prompt(opts: dict) -> str:
    """Compose system prompt from agent options."""
    if opts.get('system_prompt'):
        return opts['system_prompt']
    
    # Simple default - everything else handled in respond node
    identity = opts.get('identity', 'a helpful AI assistant')
    return f"You are {identity}."


class Agent:
    """Magical Agent - cognitive AI made simple.
    
    Clean API:
    - Agent(name, trace=True, verbose=True) - beautiful flags
    - run(): Returns result with optional streaming
    - stream(): Returns async iterator for custom handling
    """
    
    def __init__(self, name: str, trace: bool = False, verbose: bool = True, **opts):
        self.name = name
        self.trace = trace
        self.verbose = verbose
        
        # Handle memory flag - clean API for memory control
        memory_enabled = opts.get('memory', True)  # Default: enabled
        if memory_enabled:
            # Memory enabled: create backend and add Recall tool
            memory_backend = opts.get('memory_backend') or FilesystemBackend(opts.get('memory_dir', '.cogency/memory'))
        else:
            # Memory disabled: no backend, no recall
            memory_backend = None
        
        # Handle tools - only accept instances, not classes
        tools = opts.get('tools')
        if tools is not None:
            # Validate that all tools are instances, not classes
            for tool in tools:
                if isinstance(tool, type):
                    raise ValueError(f"Tool {tool.__name__} must be instantiated. Use {tool.__name__}() instead of {tool.__name__}")
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
        llm = opts.get('llm') or auto_detect_llm()
        
        self.flow = Flow(
            llm=llm,
            tools=tools,
            memory=memory_backend,
            system_prompt=compose_system_prompt(opts),
            identity=opts.get('identity'),
            json_schema=opts.get('json_schema')
        )
        self.runner = StreamingRunner()
        self.contexts = {}
        self.last_output_manager = None  # Store for get_traces()
        
        # MCP server setup if enabled
        if opts.get('enable_mcp'):
            try:
                from cogency.mcp.server import CogencyMCPServer
                self.mcp_server = CogencyMCPServer(self)
            except ImportError:
                raise ImportError("MCP package required for enable_mcp=True")
        else:
            self.mcp_server = None
    
    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution - returns async iterator for custom output handling."""
        # Input validation - basic sanitization
        if not query or not query.strip():
            yield "⚠️ Empty query not allowed\n"
            return
        
        if len(query) > 10000:  # Reasonable limit
            yield "⚠️ Query too long (max 10,000 characters)\n"
            return
        
        # Basic prompt injection detection
        suspicious_patterns = [
            "ignore previous", "forget", "system:", "assistant:", 
            "<s>", "</s>", "\n\nHuman:", "\n\nAssistant:"
        ]
        if any(pattern in query.lower() for pattern in suspicious_patterns):
            yield "⚠️ Suspicious input detected\n"
            return
        
        # Get or create context
        context = self.contexts.get(user_id) or Context(query, user_id=user_id)
        context.current_input = query
        context.add_message("user", query)  # Add user query to message history
        self.contexts[user_id] = context
        
        # Create streaming callback
        message_queue = asyncio.Queue()
        
        async def streaming_callback(message: str):
            """Clean streaming callback for all output."""
            await message_queue.put(message)
        
        # Create OutputManager with clean flags
        output_manager = OutputManager(
            trace=self.trace,
            verbose=self.verbose,
            callback=streaming_callback
        )
        
        # Store for get_traces()
        self.last_output_manager = output_manager
        
        # Clean state - zero ceremony
        state = AgentState(
            context=context,
            query=query,
            output=output_manager
        )
        
        # Start execution in background
        execution_task = asyncio.create_task(
            self.runner.stream_execute(self.flow.flow, state, streaming_callback)
        )
        
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
        """Run agent and return final response."""
        chunks = []
        async for chunk in self.stream(query, user_id):
            if "🤖 " in chunk:
                chunks.append(chunk.split("🤖 ", 1)[1])
        return "".join(chunks).strip() or "No response generated"
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """Get collected trace entries from last execution."""
        if self.last_output_manager:
            return self.last_output_manager.get_traces()
        return []
    
    # MCP compatibility methods
    async def process_input(self, input_text: str, context: Optional[Context] = None) -> str:
        return await self.run(input_text, context.user_id if context else "default")
    
    async def start_mcp_server(self, transport: str = "stdio", host: str = "localhost", port: int = 8765):
        if not self.mcp_server:
            raise ValueError("MCP server not enabled. Set enable_mcp=True in Agent constructor")
        if transport == "stdio":
            async with self.mcp_server.serve_stdio():
                pass
        elif transport == "websocket":
            await self.mcp_server.serve_websocket(host, port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")