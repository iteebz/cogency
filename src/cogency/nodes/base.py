"""Base node interface for clean cognitive architecture."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, TypedDict

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState


class BaseNode(ABC):
    """Base class for cognitive nodes.
    
    Each node represents an atomic cognitive operation.
    
    Design principles:
    - Nodes are stateless and composable
    - Primary interface is invoke() for clean, testable execution
    - Optional streaming for real-time UX
    - Compatible with LangGraph workflows
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
    async def invoke(self, state: AgentState, llm: BaseLLM, tools: List[BaseTool]) -> AgentState:
        """Execute node and return updated state.
        
        This is the primary interface - clean, testable execution.
        
        Args:
            state: Current agent state
            llm: Language model instance
            tools: Available tools
            
        Returns:
            AgentState: Updated agent state after node execution
        """
        pass
    
# No streaming method needed - LangGraph handles this
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get node metadata for introspection and debugging."""
        return {
            "name": self.name,
            "description": self.description,
            "class": self.__class__.__name__
        }