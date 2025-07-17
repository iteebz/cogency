from typing import List, Optional, Dict, Any

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import MemoryBackend
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.common.types import AgentState, OutputMode, ExecutionTrace
from cogency.workflow import Workflow
from cogency.utils.tracing import Tracer
from cogency.core.metrics import with_metrics, counter, histogram, get_metrics
from cogency.core.resilience import RateLimitedError, CircuitOpenError
from cogency.core.expression import compose_system_prompt
try:
    from cogency.core.mcp_server import CogencyMCPServer
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
# from cogency.core.monitoring import get_monitor  # Temporarily disabled for faster startup


class Agent:
    """
    Magical 6-line DX that just works.
    
    Args:
        name: Agent identifier
        personality: Core character/identity
        system_prompt: Direct LLM system message (overrides defaults)
        tone: Emotional flavor (friendly, professional, casual)
        style: Communication approach (conversational, technical, narrative)
        llm: Language model instance  
        tools: Optional list of tools for agent to use
        trace: Enable execution tracing for debugging (default: True)
    """
    def __init__(
        self,
        name: str,
        personality: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tone: Optional[str] = None,
        style: Optional[str] = None,
        llm: Optional[BaseLLM] = None,
        tools: Optional[List[BaseTool]] = None,
        trace: bool = True,
        memory: Optional[MemoryBackend] = None,
        memory_dir: str = ".memory",
        default_output_mode: OutputMode = "summary",
        enable_mcp: bool = False,
        conversation_history: bool = True,
        max_history: int = 10,
        # Internal parameters
        _response_shaper: Optional[Dict[str, Any]] = None,
    ):
        # Core setup
        self.name = name
        self.llm = llm or auto_detect_llm()
        self.memory = memory or FilesystemBackend(memory_dir)
        self.default_output_mode = default_output_mode
        
        # Four orthogonal axes of expression
        composed_system_prompt = compose_system_prompt(personality, system_prompt, tone, style)
        
        # Conversation history
        self.conversation_history_enabled = conversation_history
        self.conversation_max_history = max_history
        self.user_contexts: Dict[str, Context] = {}
        
        # Auto-discover or use provided tools
        self.tools = tools or ToolRegistry.get_tools(memory=self.memory)
        
        # Build cognitive workflow
        self.trace = trace
        self.workflow_builder = Workflow(
            self.llm, 
            self.tools, 
            self.memory, 
            system_prompt=composed_system_prompt,
            response_shaper=_response_shaper
        )
        self.workflow = self.workflow_builder.workflow
        
        # Optional MCP server
        if enable_mcp and not MCP_AVAILABLE:
            raise ImportError("MCP is required for enable_mcp=True but mcp package is not installed")
        self.mcp_server = CogencyMCPServer(self) if enable_mcp else None
    
    @with_metrics("agent.stream", tags={"agent": "stream"})
    async def stream(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None, user_id: Optional[str] = None):
        """Stream agent execution with real-time phase updates."""
        counter("agent.stream.requests")
        histogram("agent.stream.query_length", len(query))
        
        # Get user-scoped context if not provided
        if context is None:
            context = self._get_user_context(user_id, query)
        
        state = self._init_state(query, context)
        
        # Create streaming buffer for real-time updates
        streaming_buffer = []
        
        async def streaming_callback(update: str):
            """Callback to capture streaming updates in real-time."""
            streaming_buffer.append(update)
        
        # Configure streaming callback - store in configurable field
        config = {"configurable": {"streaming_callback": streaming_callback}}
        
        try:
            # Run workflow with streaming callback
            async for event in self.workflow.astream(state, config=config):
                # Yield any buffered streaming updates
                while streaming_buffer:
                    yield streaming_buffer.pop(0)
                
                if event and "react_loop" in event:
                    # Extract final reasoning content
                    reasoning_output = event["react_loop"].get("last_node_output")
                    if reasoning_output:
                        yield f"\n📝 {reasoning_output}"
            
            # Yield any remaining buffered updates
            while streaming_buffer:
                yield streaming_buffer.pop(0)
            
            counter("agent.stream.success")
            
        except RateLimitedError as e:
            counter("agent.stream.rate_limited")
            raise
        except CircuitOpenError as e:
            counter("agent.stream.circuit_open")
            raise
        except Exception as e:
            counter("agent.stream.errors")
            raise
    
    async def run_streaming(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None):
        """Run agent with beautiful streaming output to console - perfect for demos."""
        async for chunk in self.stream(query, context, mode):
            print(chunk, end="", flush=True)
        print()  # Final newline
    
    @with_metrics("agent.run", tags={"agent": "run"})
    async def run(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None, user_id: Optional[str] = None) -> str:
        """Run agent - wrapper around streaming for final response."""
        counter("agent.run.requests")
        histogram("agent.run.query_length", len(query))
        
        try:
            # Get user-scoped context or use provided context
            if context is None:
                context = self._get_user_context(user_id, query)
            
            final_response_chunks = []
            async for chunk in self.stream(query, context, mode):
                # Only collect final response chunks, not streaming updates
                if "📝 " in chunk:
                    # Extract content after the 📝 prefix
                    final_response_chunks.append(chunk.split("📝 ", 1)[1])
            
            final_response = "".join(final_response_chunks) if final_response_chunks else "No response generated"
            histogram("agent.run.response_length", len(final_response))
            
            # Store conversation turn if history is enabled
            if self.conversation_history_enabled and context:
                context.add_conversation_turn(query, final_response)
            
            # Output based on mode
            output_mode = mode or self.default_output_mode
            if self.trace:
                # Create minimal trace for output
                trace = ExecutionTrace()
                tracer = Tracer(trace)
                tracer.output(output_mode)
            
            counter("agent.run.success")
            return final_response
            
        except Exception as e:
            counter("agent.run.errors")
            raise
    
    def _init_state(self, query: str, context: Optional[Context] = None) -> AgentState:
        """Initialize agent state."""
        if context is None:
            context = Context(
                current_input=query,
                max_history=self.conversation_max_history if self.conversation_history_enabled else None,
                user_id="default"
            )
        else:
            context.current_input = query
        
        trace = ExecutionTrace()
        return {
            "query": query,
            "trace": trace,
            "context": context,
        }
    
    def _extract_response(self, result) -> str:
        """Extract final response from agent state."""
        # Check if the last action was a recall tool and format its output
        if "act" in result and "tool_output" in result["act"] and "recall_tool" in result["act"]["tool_output"] and result["act"]["tool_output"]["recall_tool"] is not None:
            recall_results = result["act"]["tool_output"]["recall_tool"].get("results", [])
            if recall_results:
                return "Recalled memories: " + " | ".join([r["content"] for r in recall_results])
            else:
                return "No relevant memories recalled."

        messages = [] # Initialize messages to empty list

        # If top-level context exists, use it
        if "context" in result:
            messages = result["context"].messages
        # Else fallback to the 'respond' node output (if context is not directly available)
        elif "respond" in result and "context" in result["respond"]:
            messages = result["respond"]["context"].messages

        # Prioritize response from the 'respond' node
        if "respond" in result and "response" in result["respond"]:
            return result["respond"]["response"]

        # Fallback to messages if no direct response from 'respond' node
        return messages[-1]["content"] if messages else "No response generated"
    
    def _estimate_query_complexity(self, query: str) -> float:
        """Estimate query complexity for monitoring."""
        complexity_score = 0.0
        
        # Length factor
        complexity_score += min(0.3, len(query) / 300)
        
        # Complexity keywords
        complex_keywords = ['analyze', 'compare', 'evaluate', 'research', 'comprehensive', 'detailed']
        simple_keywords = ['what', 'when', 'where', 'who', 'define', 'is', 'are']
        
        complex_count = sum(1 for keyword in complex_keywords if keyword in query.lower())
        simple_count = sum(1 for keyword in simple_keywords if keyword in query.lower())
        
        complexity_score += min(0.4, complex_count * 0.1)
        complexity_score -= min(0.2, simple_count * 0.05)
        
        # Question complexity
        complexity_score += min(0.2, query.count('?') * 0.1)
        complexity_score += min(0.1, query.count(' and ') * 0.05)
        
        return max(0.1, min(1.0, complexity_score))
    
    async def process_input(self, input_text: str, context: Optional[Context] = None) -> str:
        """Process input text and return response - used by MCP server"""
        return await self.run(input_text, context)
    
    async def start_mcp_server(self, transport: str = "stdio", host: str = "localhost", port: int = 8765):
        """Start MCP server for agent communication"""
        if not self.mcp_server:
            raise ValueError("MCP server not enabled. Set enable_mcp=True in Agent constructor")
        
        if transport == "stdio":
            async with self.mcp_server.serve_stdio():
                pass
        elif transport == "websocket":
            await self.mcp_server.serve_websocket(host, port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    
    def get_conversation_history(self, context: Optional[Context] = None, n: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        if not self.conversation_history_enabled:
            return []
        if context and hasattr(context, 'conversation_history'):
            return context.get_recent_conversation(n)
        return []
    
    def clear_conversation_history(self, context: Optional[Context] = None, user_id: Optional[str] = None):
        """Clear conversation history."""
        if not self.conversation_history_enabled:
            return
        if context and hasattr(context, 'conversation_history'):
            context.clear_conversation_history()
        elif user_id and user_id in self.user_contexts:
            self.user_contexts[user_id].clear_conversation_history()
    
    def _get_user_context(self, user_id: Optional[str], query: str) -> Context:
        """Get or create user-scoped context with backward compatibility."""
        # Use "default" as fallback user_id for backward compatibility
        effective_user_id = user_id or "default"
        
        if not self.conversation_history_enabled:
            # No history - create fresh context each time
            return Context(current_input=query, user_id=effective_user_id)
        
        if effective_user_id not in self.user_contexts:
            self.user_contexts[effective_user_id] = Context(
                current_input=query,
                max_history=self.conversation_max_history,
                user_id=effective_user_id
            )
        else:
            # Update existing context with new input
            self.user_contexts[effective_user_id].current_input = query
        
        return self.user_contexts[effective_user_id]
    
