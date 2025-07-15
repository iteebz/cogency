from typing import AsyncIterator, List, Optional, Union, Dict

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.tools import memory  # Import to trigger tool registration
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState
from cogency.trace import ExecutionTrace
from cogency.workflow import Flow


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
    ):
        self.name = name
        self.llm = llm if llm is not None else auto_detect_llm()
        self.memory = FSMemory(memory_dir)
        
        # Auto-discover tools including memory tools
        discovered_tools = ToolRegistry.get_tools(memory=self.memory)
        self.tools = (tools if tools is not None else []) + discovered_tools
        
        self.trace = trace
        self.workflow = Flow(self.llm, self.tools, prompt_fragments=prompt_fragments).workflow
    
    async def run(self, message: str, context: Optional[Context] = None) -> str:
        """Run agent with beautiful streaming traces by default."""
        state = self._prepare_state(message, context)
        
        # Show user query immediately
        if self.trace:
            print(f"🤖 Query: \"{message}\"")
            print()
        
        final_response = ""
        async for chunk in self.workflow.astream(state):
            for node_name, node_output in chunk.items():
                # Real-time trace display as each node completes
                if self.trace and "execution_trace" in node_output:
                    trace = node_output["execution_trace"] 
                    if trace.steps:
                        latest_step = trace.steps[-1]
                        print(latest_step)
                
                # Collect final response
                if "context" in node_output and node_output["context"].messages:
                    final_response = self._extract_response(node_output)
        
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
    
    async def stream(self, message: str, context: Optional[Context] = None) -> AsyncIterator[str]:
        """Stream the agent's response in real-time with beautiful traces."""
        state = self._prepare_state(message, context)
        
        # Show user query immediately if tracing
        if self.trace:
            print(f"🤖 Query: \"{message}\"")
            print()
        
        async for chunk in self.workflow.astream(state):
            for node_name, node_output in chunk.items():
                # Show trace for each node completion
                if self.trace and "execution_trace" in node_output:
                    trace = node_output["execution_trace"] 
                    if trace.steps:
                        latest_step = trace.steps[-1]
                        print(latest_step)
                
                # Only stream final response from RESPOND node
                if node_name == "respond" and "context" in node_output:
                    response = self._extract_response(node_output)
                    if response and response != "No response generated":
                        for char in response:
                            yield char
    
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
    
