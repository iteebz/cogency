"""Cognitive flow abstraction for clean Agent DX."""
from functools import partial
from typing import Dict, List, Callable, Optional, Any

from langgraph.graph import StateGraph, END
from cogency.nodes.preprocess import preprocess_node
from cogency.nodes.reason import reason_node
from cogency.nodes.act import act_node
from cogency.nodes.respond import respond_node
from cogency.types import AgentState, OutputMode
from cogency.memory.core import MemoryBackend


# Clean 4-node cognitive flow - PROPER SEPARATION
DEFAULT_ROUTING_TABLE = {
    "entry_point": "preprocess",
    "edges": {
        "preprocess": {"type": "conditional", "condition": "_route_from_preprocess"},
        "reason": {"type": "conditional", "condition": "_route_from_reason"},
        "act": {"type": "conditional", "condition": "_route_from_act"},
        "respond": {"type": "end"}
    }
}


class Flow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, memory: MemoryBackend, routing_table: Optional[Dict] = None, identity: Optional[str] = None, json_schema: Optional[str] = None, system_prompt: Optional[str] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.identity = identity
        self.json_schema = json_schema
        self.system_prompt = system_prompt
        self.flow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive flow graph from routing table - PURE ORCHESTRATION."""
        flow = StateGraph(AgentState)
        
        # Pure LangGraph composition - nodes handle their own dependencies
        node_functions = {
            "preprocess": partial(preprocess_node, llm=self.llm, tools=self.tools, memory=self.memory, system_prompt=self.system_prompt),
            "reason": partial(reason_node, llm=self.llm, tools=self.tools, system_prompt=self.system_prompt),
            "act": partial(act_node, tools=self.tools),
            "respond": partial(respond_node, llm=self.llm, system_prompt=self.system_prompt, identity=self.identity, json_schema=self.json_schema)
        }
        
        # Add nodes to flow
        for node_name, node_func in node_functions.items():
            flow.add_node(node_name, node_func)
        
        # Configure edges from routing table
        flow.set_entry_point(self.routing_table["entry_point"])
        
        # Add conditional routing functions
        flow.add_conditional_edges("preprocess", _route_from_preprocess)
        flow.add_conditional_edges("reason", _route_from_reason)
        flow.add_conditional_edges("act", _route_from_act)
        flow.add_edge("respond", END)
        
        return flow.compile()


def _route_from_preprocess(state: AgentState) -> str:
    """Route from preprocess based on next_node decision."""
    return state.get("next_node", "reason")


def _route_from_reason(state: AgentState) -> str:
    """Route from reason based on next_node decision."""
    return state.get("next_node", "respond")


def _route_from_act(state: AgentState) -> str:
    """Route from act - always returns to reason for reflection."""
    return state.get("next_node", "reason")