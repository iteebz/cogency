"""Cognitive workflow abstraction for clean Agent DX."""
from functools import partial
from typing import Dict, List, Callable, Optional

from langgraph.graph import StateGraph, END
from cogency.nodes.react_loop import react_loop_node
from cogency.nodes.memory import memorize
from cogency.nodes.select_tools import select_tools
from cogency.types import AgentState, OutputMode
from cogency.memory.base import BaseMemory
from cogency.constants import NodeName


# Linear 3-node cognitive flow - ZERO CEREMONY
DEFAULT_ROUTING_TABLE = {
    "entry_point": NodeName.MEMORIZE.value,
    "edges": {
        NodeName.MEMORIZE.value: {"type": "direct", "destination": NodeName.SELECT_TOOLS.value},
        NodeName.SELECT_TOOLS.value: {"type": "direct", "destination": NodeName.REACT_LOOP.value},
        NodeName.REACT_LOOP.value: {"type": "end"}
    }
}


class Workflow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, memory: BaseMemory, routing_table: Optional[Dict] = None, prompt_fragments: Optional[Dict[str, Dict[str, str]]] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.prompt_fragments = prompt_fragments or {}
        # Mode is now handled in Agent class
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive workflow graph from routing table - PURE ORCHESTRATION."""
        workflow = StateGraph(AgentState)
        
        # Pure LangGraph composition - nodes handle their own dependencies
        node_functions = {
            NodeName.MEMORIZE.value: partial(memorize, memory=self.memory),
            NodeName.SELECT_TOOLS.value: partial(select_tools, llm=self.llm, tools=self.tools),
            NodeName.REACT_LOOP.value: partial(react_loop_node, llm=self.llm, tools=self.tools, prompt_fragments=self.prompt_fragments.get("react_loop", {}))
        }
        
        # Add nodes to workflow
        for node_name, node_func in node_functions.items():
            workflow.add_node(node_name, node_func)
        
        # Configure edges from routing table
        workflow.set_entry_point(self.routing_table["entry_point"])
        
        for node_name, edge_config in self.routing_table["edges"].items():
            if edge_config["type"] == "direct":
                workflow.add_edge(node_name, edge_config["destination"])
            elif edge_config["type"] == "end":
                workflow.add_edge(node_name, END)
        
        return workflow.compile()