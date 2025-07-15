"""Cognitive workflow abstraction for clean Agent DX."""
from functools import partial
from typing import Dict, List, Callable, Optional

from langgraph.graph import StateGraph, END
from cogency.nodes.reason import reason
from cogency.nodes.respond import respond
from cogency.nodes.memory import memorize
from cogency.nodes.select_tools import select_tools
from cogency.types import AgentState, OutputMode
from cogency.memory.base import BaseMemory
from cogency.router import Router
from cogency.constants import NodeName


# Simplified cognitive flow - NO CEREMONY
DEFAULT_ROUTING_TABLE = {
    "entry_point": NodeName.MEMORIZE.value,
    "edges": {
        NodeName.MEMORIZE.value: {"type": "direct", "destination": NodeName.SELECT_TOOLS.value},
        NodeName.SELECT_TOOLS.value: {"type": "direct", "destination": NodeName.REASON.value},
        NodeName.REASON.value: {"type": "conditional", "router": "_route", "destinations": {NodeName.RESPOND.value: NodeName.RESPOND.value}},
        NodeName.RESPOND.value: {"type": "end"}
    }
}


class Flow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, memory: BaseMemory, routing_table: Optional[Dict] = None, prompt_fragments: Optional[Dict[str, Dict[str, str]]] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.router = Router(tools=self.tools)  # Instantiate the Router
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
            NodeName.REASON.value: partial(reason, llm=self.llm, tools=self.tools, prompt_fragments=self.prompt_fragments.get("reason", {})),
            NodeName.RESPOND.value: partial(respond, llm=self.llm)
        }
        
        # Add nodes to workflow
        for node_name, node_func in node_functions.items():
            workflow.add_node(node_name, node_func)
        
        # Configure edges from routing table
        workflow.set_entry_point(self.routing_table["entry_point"])
        
        for node_name, edge_config in self.routing_table["edges"].items():
            if edge_config["type"] == "direct":
                workflow.add_edge(node_name, edge_config["destination"])
            elif edge_config["type"] == "conditional":
                router_func = getattr(self, edge_config["router"])
                workflow.add_conditional_edges(node_name, router_func, edge_config["destinations"])
            elif edge_config["type"] == "end":
                workflow.add_edge(node_name, END)
        
        return workflow.compile()
    
    def _route(self, state: AgentState) -> str:
        """Universal router - simplified for reason-based flow."""
        return self.router.route(state)