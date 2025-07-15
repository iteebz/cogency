"""Cognitive workflow abstraction for clean Agent DX."""
from functools import partial
from typing import Dict, List, Callable, Optional

from langgraph.graph import StateGraph, END
from cogency.nodes import think, plan, act, reflect, respond
from cogency.types import AgentState, StreamingMode
from cogency.utils import parse_plan, parse_reflect


# Default cognitive flow configuration - TPARR workflow
DEFAULT_ROUTING_TABLE = {
    "entry_point": "think",
    "edges": {
        "think": {"type": "conditional", "router": "_route_think", "destinations": {"plan": "plan", "respond": "respond"}},
        "plan": {"type": "conditional", "router": "_route", "destinations": {"respond": "respond", "act": "act"}},
        "act": {"type": "direct", "destination": "reflect"},
        "reflect": {"type": "conditional", "router": "_route", "destinations": {"respond": "respond", "plan": "plan"}},
        "respond": {"type": "end"}
    }
}


class Flow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, routing_table: Optional[Dict] = None, prompt_fragments: Optional[Dict[str, Dict[str, str]]] = None):
        self.llm = llm
        self.tools = tools
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.prompt_fragments = prompt_fragments or {}
        self.stream_mode = "summary"  # Default mode
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive workflow graph from routing table - PURE ORCHESTRATION."""
        workflow = StateGraph(AgentState)
        
        # Pure LangGraph composition - nodes handle their own dependencies
        node_functions = {
            "think": partial(think, llm=self.llm),
            "plan": partial(plan, llm=self.llm, tools=self.tools, prompt_fragments=self.prompt_fragments.get("plan", {})),
            "act": partial(act, tools=self.tools),
            "reflect": partial(reflect, llm=self.llm),
            "respond": partial(respond, llm=self.llm)
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
    
    def _route_think(self, state: AgentState) -> str:
        """Router for THINK phase - determines if we need planning or can respond directly."""
        # Check if thinking determined this is a simple query
        if state.get("skip_thinking"):
            return "respond"
        
        # Check the thinking output to see if it indicates tools are needed
        last_message = state["context"].messages[-1]["content"]
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""
        
        # Look for indicators that tools/planning are needed
        thinking_indicators = ["tool", "search", "calculate", "remember", "complex", "step", "analyze", "need to"]
        
        if any(indicator in last_message.lower() for indicator in thinking_indicators):
            return "plan"
        
        # If tools are available and thinking suggests complexity, go to plan
        if len(self.tools) > 0 and any(word in last_message.lower() for word in ["analyze", "research", "find", "look up", "check"]):
            return "plan"
        
        # Otherwise, go straight to respond
        return "respond"
    
    def _route(self, state: AgentState) -> str:
        """Universal router for plan/reflect decisions."""
        last_message = state["context"].messages[-1]["content"]
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""
        
        # Try plan routing first
        plan_data = parse_plan(last_message)
        if plan_data:
            action = plan_data.get("action")
            if action == "tool_needed":
                return "act"
            elif action == "direct_response":
                return "respond"
        
        # Try reflect routing
        reflect_data = parse_reflect(last_message)
        if reflect_data:
            status = reflect_data.get("status")
            if status == "continue":
                return "plan"
            elif status == "complete":
                return "respond"
        
        # Default fallback
        return "respond"