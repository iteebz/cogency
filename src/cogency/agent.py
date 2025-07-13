from typing import AsyncIterator, List, Optional, Union

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.memory import tools  # Import to trigger tool registration
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState, ExecutionTrace
from cogency.workflow import CognitiveWorkflow


class Agent:
    """
    Magical 6-line DX that just works.
    
    Args:
        name: Agent identifier
        llm: Language model instance  
        tools: Optional list of tools for agent to use
        trace: Enable execution tracing for debugging (default: False)
    """
    def __init__(
        self,
        name: str,
        llm: Optional[BaseLLM] = None,
        tools: Optional[List[BaseTool]] = None,
        trace: bool = False,
        memory_dir: str = ".cogency_memory",
    ):
        self.name = name
        self.llm = llm if llm is not None else auto_detect_llm()
        self.memory = FSMemory(memory_dir)
        
        # Auto-discover tools including memory tools
        discovered_tools = ToolRegistry.get_tools(memory=self.memory)
        self.tools = (tools if tools is not None else []) + discovered_tools
        
        self.trace = trace
        self.workflow = CognitiveWorkflow(self.llm, self.tools).workflow
    
    async def run(self, message: str, context: Optional[Context] = None) -> str:
        """Run agent in batch mode."""
        state = self._prepare_state(message, context)
        result = await self.workflow.ainvoke(state)
        return self._extract_response(result)
    
    async def stream(self, message: str, context: Optional[Context] = None) -> AsyncIterator[str]:
        """Stream the agent's response in real-time."""
        state = self._prepare_state(message, context)
        async for chunk in self.workflow.astream(state):
            for node_name, node_output in chunk.items():
                # Extract final response from any terminal node
                if "context" in node_output and node_output["context"].messages:
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
        
        execution_trace = ExecutionTrace(trace_id=f"{self.name}_{message[:20]}") if self.trace else None
        return {"context": context, "execution_trace": execution_trace}
    
    def _extract_response(self, result) -> str:
        """Extract final response from agent state."""
        messages = result["context"].messages
        return messages[-1]["content"] if messages else "No response generated"
    
