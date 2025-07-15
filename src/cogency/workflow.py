"""Cognitive workflow abstraction for clean Agent DX."""
from typing import Dict, List, Callable, Optional

from langgraph.graph import StateGraph, END
from cogency.nodes import plan, reason, act, reflect, respond
from cogency.types import AgentState
from cogency.utils.parsing import parse_plan_response, parse_reflect_response


# Default cognitive flow configuration
DEFAULT_ROUTING_TABLE = {
    "entry_point": "plan",
    "edges": {
        "plan": {"type": "conditional", "router": "_route", "destinations": {"respond": "respond", "reason": "reason"}},
        "reason": {"type": "direct", "destination": "act"},
        "act": {"type": "direct", "destination": "reflect"},
        "reflect": {"type": "conditional", "router": "_route", "destinations": {"respond": "respond", "reason": "reason"}},
        "respond": {"type": "end"}
    }
}


class CognitiveWorkflow:
    """Abstracts LangGraph complexity for magical Agent DX."""
    
    def __init__(self, llm, tools, routing_table: Optional[Dict] = None, prompt_fragments: Optional[Dict[str, Dict[str, str]]] = None):
        self.llm = llm
        self.tools = tools
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.prompt_fragments = prompt_fragments or {}
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive workflow graph from routing table."""
        workflow = StateGraph(AgentState)
        
        # Register function-based nodes
        node_functions = {
            "plan": plan,
            "reason": reason, 
            "act": act,
            "reflect": reflect,
            "respond": respond
        }
        
        for node_name, node_func in node_functions.items():
            workflow.add_node(node_name, self._wrap_node(node_name, node_func))
        
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
    
    def _wrap_node(self, node_name: str, node_func):
        """Wrap function-based node for LangGraph execution, dynamically passing arguments."""
        import inspect
        from datetime import datetime

        async def wrapped(state: AgentState) -> AgentState:
            sig = inspect.signature(node_func)
            
            available_args = {
                "llm": self.llm,
                "tools": self.tools,
                "prompt_fragments": self.prompt_fragments.get(node_name, {})
            }
            
            args_to_pass = {}
            for param_name, _ in sig.parameters.items():
                if param_name == "state":
                    continue  # State is always passed positionally
                if param_name in available_args:
                    args_to_pass[param_name] = available_args[param_name]
            
            result = await node_func(state, **args_to_pass)
            
            # BEAUTIFUL AUTO-TRACING - zero ceremony
            if state.get("execution_trace"):
                context = result.get("context") if isinstance(result, dict) else None
                state["execution_trace"].add(node_name.lower(), context)
            
            return result
        return wrapped
    
    def _route(self, state: AgentState) -> str:
        """Universal router for plan/reflect decisions."""
        last_message = state["context"].messages[-1]["content"]
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""
        
        # Try plan routing first
        route, _ = parse_plan_response(last_message)
        
        # If plan doesn't route to respond, it means it wants to reason (i.e., use a tool)
        # If it routes to respond, then we check reflect for further routing
        if route == "respond":
            route, _ = parse_reflect_response(last_message)
        
        return route