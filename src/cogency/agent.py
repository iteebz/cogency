from typing import List, Optional, Dict

from cogency.context import Context
from cogency.llm import BaseLLM, auto_detect_llm
from cogency.memory.filesystem import FSMemory
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.types import AgentState, OutputMode, ExecutionTrace
from cogency.workflow import Workflow
from cogency.core.tracer import Tracer
# from cogency.core.monitoring import get_monitor  # Temporarily disabled for faster startup


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
        self.workflow_builder = Workflow(self.llm, self.tools, self.memory, prompt_fragments=prompt_fragments)
        self.workflow = self.workflow_builder.workflow
        # self.monitor = get_monitor()  # Temporarily disabled for faster startup
    
    async def stream(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None):
        """Stream agent execution with native LangGraph streaming."""
        state = self._init_state(query, context)
        
        # Use native LangGraph streaming
        async for event in self.workflow.astream(state):
            if event and "react_loop" in event:
                # Extract reasoning content from node output
                reasoning_output = event["react_loop"].get("last_node_output")
                if reasoning_output:
                    yield reasoning_output
    
    async def run(self, query: str, context: Optional[Context] = None, mode: Optional[OutputMode] = None) -> str:
        """Run agent - wrapper around streaming for final response."""
        response_chunks = []
        async for chunk in self.stream(query, context, mode):
            response_chunks.append(chunk)
        
        final_response = "".join(response_chunks) if response_chunks else "No response generated"
        
        # Output based on mode
        output_mode = mode or self.default_output_mode
        if self.trace:
            # Create minimal trace for output
            trace = ExecutionTrace()
            tracer = Tracer(trace)
            tracer.output(output_mode)
        
        return final_response
    
    def _init_state(self, query: str, context: Optional[Context] = None) -> AgentState:
        """Initialize agent state."""
        if context is None:
            context = Context(current_input=query)
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
    
