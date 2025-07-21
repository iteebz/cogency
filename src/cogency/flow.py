"""Cognitive flow abstraction."""

from functools import partial
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from cogency.memory.core import MemoryBackend
from cogency.nodes.act import act
from cogency.nodes.preprocess import preprocess
from cogency.nodes.reason import reason
from cogency.nodes.respond import respond
from cogency.state import State

# Clean 4-node cognitive flow - PROPER SEPARATION
DEFAULT_ROUTING_TABLE = {
    "entry_point": "preprocess",
    "edges": {
        "preprocess": {"type": "conditional", "condition": "_route_from_preprocess"},
        "reason": {"type": "conditional", "condition": "_route_from_reason"},
        "act": {"type": "conditional", "condition": "_route_from_act"},
        "respond": {"type": "end"},
    },
}


class Flow:
    """LangGraph wrapper for agent workflow."""

    def __init__(
        self,
        llm: Any,
        tools: Any,
        memory: Optional[MemoryBackend],
        routing_table: Optional[Dict[str, Any]] = None,
        identity: Optional[str] = None,
        json_schema: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.routing_table = routing_table or DEFAULT_ROUTING_TABLE
        self.identity = identity
        self.json_schema = json_schema
        self.system_prompt = system_prompt
        self.flow = self._build()

    def _build(self) -> Any:
        """Build flow graph from routing table."""
        flow = StateGraph(State)

        # Pure LangGraph composition - nodes handle their own dependencies
        node_functions: Dict[str, Any] = {}

        if self.memory is not None:
            node_functions["preprocess"] = partial(
                preprocess,
                llm=self.llm,
                tools=self.tools,
                memory=self.memory,
                system_prompt=self.system_prompt or "",
            )
        else:
            # Create a no-op preprocess when memory is None
            async def preprocess_no_memory(state: State, **kwargs: Any) -> State:
                state["next_node"] = "reason"
                return state

            node_functions["preprocess"] = preprocess_no_memory

        node_functions.update(
            {
                "reason": partial(
                    reason, llm=self.llm, tools=self.tools, system_prompt=self.system_prompt or ""
                ),
                "act": partial(act, tools=self.tools),
                "respond": partial(
                    respond,
                    llm=self.llm,
                    system_prompt=self.system_prompt or "",
                    identity=self.identity,
                    json_schema=self.json_schema,
                ),
            }
        )

        # Add nodes to flow
        for node_name, node_func in node_functions.items():
            flow.add_node(node_name, node_func)

        # Configure edges from routing table
        entry_point = self.routing_table["entry_point"]
        if isinstance(entry_point, str):
            flow.set_entry_point(entry_point)

        # Add conditional routing functions
        flow.add_conditional_edges("preprocess", _route_from_preprocess)
        flow.add_conditional_edges("reason", _route_from_reason)
        flow.add_conditional_edges("act", _route_from_act)
        flow.add_edge("respond", END)

        return flow.compile()


def _route_from_preprocess(state: State) -> str:
    """Route from preprocess node."""
    next_node = state.get("next_node", "reason")
    return str(next_node)


def _route_from_reason(state: State) -> str:
    """Route from reason node."""
    next_node = state.get("next_node", "respond")
    return str(next_node)


def _route_from_act(state: State) -> str:
    """Route from act node."""
    next_node = state.get("next_node", "reason")
    return str(next_node)
