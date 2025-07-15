from typing import AsyncIterator, List, Optional, Union, Dict
from datetime import datetime

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.tools import memory  # Import to trigger tool registration
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState, OutputMode
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
        default_output_mode: OutputMode = "summary",
    ):
        self.name = name
        self.llm = llm if llm is not None else auto_detect_llm()
        self.memory = FSMemory(memory_dir)
        self.default_output_mode = default_output_mode
        
        # Auto-discover tools including memory tools
        discovered_tools = ToolRegistry.get_tools(memory=self.memory)
        self.tools = (tools if tools is not None else []) + discovered_tools
        
        self.trace = trace
        self.flow = Flow(self.llm, self.tools, prompt_fragments=prompt_fragments)
        self.workflow = self.flow.workflow
    
    async def run(self, query: str, context: Optional[Context] = None, mode: OutputMode = "summary") -> str:
        """Run agent with clean mode control."""
        from cogency.types import ExecutionTrace, summarize_trace, format_trace, format_full_debug
        
        # Initialize state
        if context is None:
            context = Context(current_input=query)
        else:
            context.current_input = query
        
        trace = ExecutionTrace()
        state = {
            "query": query,
            "trace": trace,
            "context": context,
        }
        
        # Smart auto-storage: Store personal info without ceremony
        if hasattr(self.memory, 'should_store'):
            should_store, category = self.memory.should_store(query)
            if should_store:
                await self.memory.memorize(query, tags=[category])
        
        # Execute workflow
        final_state = None
        async for event in self.workflow.astream_events(state, version="v1"):
            if event["event"] == "on_chain_end" and event.get("name") == "LangGraph":
                # Capture final state from main workflow
                final_state = event["data"]["output"]
        
        # Extract response from final state
        if final_state:
            final_response = self._extract_response(final_state)
        else:
            final_response = "No response generated"
        
        # Output based on mode
        if mode == "summary":
            print(f"✅ {summarize_trace(trace)}")
        elif mode == "trace":
            print(format_trace(trace))
            print(f"\n✅ Complete")
        elif mode == "dev":
            print(format_full_debug(trace))
            print(f"\n✅ Complete")
        
        return final_response
    
    async def stream(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None) -> str:
        """Alias for run() - backward compatibility."""
        return await self.run(query, context, mode or self.default_output_mode)
    
    
# No longer needed - state preparation is inline in run()
    
    def _extract_response(self, result) -> str:
        """Extract final response from agent state."""
        # If top-level context exists, use it
        if "context" in result:
            messages = result["context"].messages
        # Else fallback to the 'respond' node output
        elif "respond" in result and "context" in result["respond"]:
            messages = result["respond"]["context"].messages
        else:
            return "No response generated"

        return messages[-1]["content"] if messages else "No response generated"
    
