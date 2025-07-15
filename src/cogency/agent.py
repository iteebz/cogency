from typing import List, Optional, Dict

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState, OutputMode, ExecutionTrace
from cogency.react import ReAct
from cogency.tracer import Tracer


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
        self.react = ReAct(self.llm, self.tools, self.memory, prompt_fragments=prompt_fragments)
        self.workflow = self.react.workflow
    
    async def run(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None) -> str:
        """Run agent with clean mode control."""
        
        # Initialize state
        if context is None:
            context = Context(current_input=query)
        else:
            context.current_input = query
        
        trace = ExecutionTrace()
        state: AgentState = {
            "query": query,
            "trace": trace,
            "context": context,
        }
        
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
        output_mode = mode or self.default_output_mode
        if self.trace:
            tracer = Tracer(trace)
            tracer.output(output_mode)
        
        return final_response
    
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
    
