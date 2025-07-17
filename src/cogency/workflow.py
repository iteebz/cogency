"""Cognitive workflow abstraction for clean Agent DX."""
from functools import partial
from typing import Dict, List, Callable, Optional, Any

from langgraph.graph import StateGraph, END
from cogency.react.react_responder import react_loop_node
from cogency.prepare.pre_react import pre_react_node
from cogency.common.types import AgentState, OutputMode
from cogency.memory.core import MemoryBackend
from cogency.common.constants import NodeName


# Optimized 2-node cognitive flow - MINIMAL LATENCY
DEFAULT_ROUTING_TABLE = {
    "entry_point": "pre_react",
    "edges": {
        "pre_react": {"type": "direct", "destination": NodeName.REACT_LOOP.value},
        NodeName.REACT_LOOP.value: {"type": "end"}
    }
}


class Workflow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, memory: MemoryBackend, routing_table: Optional[Dict] = None, response_shaper: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.response_shaper = response_shaper or {}
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive workflow graph from routing table - PURE ORCHESTRATION."""
        workflow = StateGraph(AgentState)
        
        # Pure LangGraph composition - nodes handle their own dependencies
        node_functions = {
            "pre_react": partial(pre_react_node, llm=self.llm, tools=self.tools, memory=self.memory),
            NodeName.REACT_LOOP.value: partial(react_loop_node, llm=self.llm, tools=self.tools, response_shaper=self.response_shaper)
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