import asyncio
from typing import Optional, AsyncIterator
from cogency.workflow import Workflow
from cogency.runner import StreamingRunner
from cogency.messaging import AgentMessenger
from cogency.context import Context
from cogency.llm import auto_detect_llm
from cogency.tools.registry import ToolRegistry
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.tracing import ExecutionTrace


def compose_system_prompt(opts: dict) -> str:
    """Compose system prompt from agent options."""
    if opts.get('system_prompt'):
        return opts['system_prompt']
    
    # Check if response_shaper has personality info
    response_shaper = opts.get('response_shaper', {})
    personality = response_shaper.get('personality') or opts.get('personality', 'a helpful AI assistant')
    
    parts = [f"You are {personality}."]
    
    # Use tone from response_shaper if available, otherwise from opts
    tone = response_shaper.get('tone') or opts.get('tone')
    style = response_shaper.get('style') or opts.get('style')
    
    if tone or style:
        style_parts = [
            f"{k}: {v}" for k, v in [
                ("tone", tone), 
                ("style", style)
            ] if v
        ]
        parts.append(f"Communicate with {', '.join(style_parts)}.")
    
    # Add constraints from response_shaper
    if response_shaper.get('constraints'):
        for constraint in response_shaper['constraints']:
            parts.append(f"{constraint.replace('-', ' ').title()}.")
    
    parts.append("Always stay in character and respond naturally.")
    return " ".join(parts)


class Agent:
    """Magical Agent - cognitive AI made simple.
    
    Primary APIs:
    - query(): Auto-prints + returns result (90% use case)  
    - stream(): Returns async iterator for custom handling
    """
    
    def __init__(self, name: str, **opts):
        self.name = name
        
        # Handle tools - instantiate if classes are passed
        tools = opts.get('tools')
        if tools:
            instantiated_tools = []
            for tool in tools:
                if isinstance(tool, type):
                    # It's a class, instantiate it
                    try:
                        instantiated_tools.append(tool())
                    except TypeError:
                        # Try with memory if needed
                        try:
                            instantiated_tools.append(tool(memory=opts.get('memory')))
                        except:
                            # Skip tools that can't be instantiated
                            continue
                else:
                    # It's already an instance
                    instantiated_tools.append(tool)
            tools = instantiated_tools
        else:
            tools = ToolRegistry.get_tools(memory=opts.get('memory'))
        
        self.workflow = Workflow(
            llm=opts.get('llm') or auto_detect_llm(),
            tools=tools,
            memory=opts.get('memory') or FilesystemBackend(opts.get('memory_dir', '.cogency/memory')),
            system_prompt=compose_system_prompt(opts),
            response_shaper=opts.get('response_shaper')
        )
        self.runner = StreamingRunner()
        self.contexts = {}
        self.trace_enabled = opts.get('trace', False)
        self.last_trace = None
        
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
        # Get or create context
        context = self.contexts.get(user_id) or Context(query, user_id=user_id)
        context.current_input = query
        context.add_message("user", query)  # Add user query to message history
        self.contexts[user_id] = context
        
        # Show user input with beautiful formatting
        yield f"👤 {query}\n"
        
        # Stream execution with clean callback
        state = {"query": query, "context": context, "trace": ExecutionTrace()}
        
        # Create a queue for streaming messages
        message_queue = asyncio.Queue()
        
        async def streaming_callback(message: str):
            """Clean streaming callback for user-facing messages."""
            await message_queue.put(message)
        
        # Start execution in background
        execution_task = asyncio.create_task(
            self.runner.stream_execute(self.workflow.workflow, state, streaming_callback)
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
            final_state = await execution_task
            self.last_trace = final_state.get("trace")
            
            # Print trace if enabled
            if self.trace_enabled and self.last_trace:
                from cogency.tracing import format_trace
                print(f"\n🔍 TRACE:\n{format_trace(self.last_trace)}")
    
    async def run(self, query: str, user_id: str = "default") -> str:
        """Run agent and return final response."""
        chunks = []
        async for chunk in self.stream(query, user_id):
            if "🤖 AGENT: " in chunk:
                chunks.append(chunk.split("🤖 AGENT: ", 1)[1])
        return "".join(chunks).strip() or "No response generated"
    
    async def query(self, query: str, user_id: str = "default") -> str:
        """Beautiful API - auto-prints streaming output + returns final response.
        
        Use this for demos and simple usage. For custom output handling, use stream().
        Both methods are streaming under the hood - this just eliminates print ceremony.
        """
        result = ""
        async for chunk in self.stream(query, user_id):
            print(chunk, end="", flush=True)
            if "🤖 AGENT: " in chunk:
                result += chunk.split("🤖 AGENT: ", 1)[1]
        return result.strip() or "No response generated"
    
    def _extract_response(self, state) -> str:
        """Extract response from final state."""
        if "respond" in state and "response" in state["respond"]:
            return state["respond"]["response"]
        if "context" in state and state["context"].messages:
            return state["context"].messages[-1].get("content", "No response")
        return "No response generated"
    
    def get_trace(self) -> Optional[str]:
        """Get formatted trace from last execution."""
        if not self.last_trace:
            return None
        from cogency.tracing import format_trace
        return format_trace(self.last_trace)
    
    def enable_tracing(self):
        """Enable tracing for debugging."""
        self.trace_enabled = True
    
    def disable_tracing(self):
        """Disable tracing."""
        self.trace_enabled = False
    
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