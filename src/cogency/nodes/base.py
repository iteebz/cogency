"""Base node interface for stream-first cognitive architecture."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, TypedDict

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState


class StreamDelta(TypedDict):
    """Structured streaming delta from cognitive nodes."""
    type: str  # thinking, chunk, result, tool_call, error, state
    node: str  # node name
    content: Optional[str]  # for thinking/chunk/error types
    data: Optional[Dict[str, Any]]  # for result/tool_call types
    state: Optional[Dict[str, Any]]  # for state type


@dataclass
class NodeContext:
    """Enhanced context for cognitive nodes with execution resources."""
    state: AgentState
    llm: Optional[BaseLLM] = None
    tools: Optional[List[BaseTool]] = None


class BaseNode(ABC):
    """Base class for pluggable cognitive nodes in stream-first architecture.
    
    Each node represents an atomic cognitive operation that yields structured
    streaming deltas to provide real-time observability into agent reasoning.
    
    Design principles:
    - Nodes are stateless and composable
    - Streaming is the primary interface, not an afterthought  
    - Rich observability through structured deltas
    - Clean separation of concerns
    - Compatible with existing LangGraph workflows
    """
    
    def __init__(self, name: str, description: str):
        """Initialize cognitive node.
        
        Args:
            name: Node identifier for routing and observability
            description: Human-readable description of node purpose
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream node execution with real-time deltas.
        
        This is the primary interface - streaming execution that yields
        structured deltas as cognition unfolds.
        
        Args:
            ctx: Node context with state, tools, LLM, etc.
            yield_interval: Minimum time between yields for rate limiting
            
        Yields:
            StreamDelta: Structured streaming chunks with types:
                - thinking: Agent's reasoning process
                - chunk: LLM response chunks  
                - result: Node execution results
                - tool_call: Tool execution events
                - error: Error events
                - state: Updated agent state
        """
        pass
    
    async def invoke(self, ctx: NodeContext) -> AgentState:
        """Non-streaming version for LangGraph compatibility.
        
        Default implementation collects streaming deltas and returns final state.
        Can be overridden for optimized non-streaming execution.
        """
        final_state = ctx.state
        async for delta in self.stream(ctx):
            if delta["type"] == "state":
                final_state = delta["state"]
        
        return final_state
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get node metadata for introspection and debugging."""
        return {
            "name": self.name,
            "description": self.description,
            "class": self.__class__.__name__
        }