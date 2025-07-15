from typing import AsyncIterator, List, Optional, Union, Dict

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.tools import memory  # Import to trigger tool registration
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState, StreamingMode
from cogency.types import ExecutionTrace
from cogency.flow import Flow


class Agent:
    """
    Magical 6-line DX that just works.
    
    Args:
        name: Agent identifier
        llm: Language model instance  
        tools: Optional list of tools for agent to use
        trace: Enable execution tracing for debugging (default: True)
    """
    def __init__(
        self,
        name: str,
        llm: Optional[BaseLLM] = None,
        tools: Optional[List[BaseTool]] = None,
        trace: bool = True,
        memory_dir: str = ".memory",
        prompt_fragments: Optional[Dict[str, Dict[str, str]]] = None,
        default_streaming_mode: StreamingMode = "summary",
    ):
        self.name = name
        self.llm = llm if llm is not None else auto_detect_llm()
        self.memory = FSMemory(memory_dir)
        self.default_streaming_mode = default_streaming_mode
        
        # Auto-discover tools including memory tools
        discovered_tools = ToolRegistry.get_tools(memory=self.memory)
        self.tools = (tools if tools is not None else []) + discovered_tools
        
        self.trace = trace
        self.flow = Flow(self.llm, self.tools, prompt_fragments=prompt_fragments)
        self.workflow = self.flow.workflow
    
    async def stream(self, message: str, context: Optional[Context] = None, mode: Optional[StreamingMode] = None) -> str:
        """STREAMING FIRST: Run agent with real-time traces."""
        mode = mode or self.default_streaming_mode
        state = self._prepare_state(message, context)
        
        # Smart auto-storage: Store personal info without ceremony
        if hasattr(self.memory, 'should_store'):
            should_store, category = self.memory.should_store(message)
            if should_store:
                await self.memory.memorize(message, tags=[category])
        
        # Show user query immediately
        if self.trace:
            print(f"🤖 Query: \"{message}\"")
            print()
        
        final_response = ""
        final_state = None
        
        # Set mode on flow for this execution
        self.flow.stream_mode = mode
        
        # Execute workflow with node-based streaming
        final_state = await self.workflow.ainvoke(state)
        
        # Extract response from final state
        if final_state and "context" in final_state:
            final_response = self._extract_response(final_state)
        else:
            final_response = "No response generated"
        
        # Show completion
        if self.trace:
            total_s = (state["execution_trace"].start_time if state.get("execution_trace") else 0)
            if isinstance(total_s, type(state["execution_trace"].start_time)):
                from datetime import datetime
                total_s = (datetime.now() - total_s).total_seconds()
                print(f"\n✅ Complete ({total_s:.1f}s)")
            else:
                print("\n✅ Complete")
        
        return final_response
    
    async def run(self, message: str, context: Optional[Context] = None) -> str:
        """BATCH MODE: Run without streaming for programmatic use."""
        # Temporarily disable tracing for batch mode
        original_trace = self.trace
        self.trace = False
        
        try:
            return await self.stream(message, context)
        finally:
            self.trace = original_trace
    
    
    def _prepare_state(self, message: str, context: Optional[Context] = None) -> AgentState:
        """Prepare agent state for execution."""
        if context is None:
            context = Context(current_input=message)
        else:
            context.current_input = message
        
        execution_trace = ExecutionTrace() if self.trace else None
        if execution_trace:
            execution_trace.user_query = f'Query: "{message}"'
        return {"context": context, "execution_trace": execution_trace}
    
    def _extract_response(self, result) -> str:
        """Extract final response from agent state."""
        messages = result["context"].messages
        return messages[-1]["content"] if messages else "No response generated"
    
