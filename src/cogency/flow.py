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

        # Always run preprocess for smart routing, even without memory
        node_functions["preprocess"] = partial(
            preprocess,
            llm=self.llm,
            tools=self.tools,
            memory=self.memory,  # Can be None
            system_prompt=self.system_prompt or "",
            identity=self.identity,
        )

        node_functions.update(
            {
                "reason": partial(
                    reason,
                    llm=self.llm,
                    tools=self.tools,
                    system_prompt=self.system_prompt or "",
                    identity=self.identity,
                ),
                "act": partial(act, tools=self.tools),
                "respond": partial(
                    respond,
                    llm=self.llm,
                    tools=self.tools,
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


async def _route_from_preprocess(state: State) -> str:
    """Route from preprocess - respond directly if no tools selected, else reason."""
    selected_tools = state.get("selected_tools")
    route = "respond" if not selected_tools else "reason"

    if hasattr(state, "output") and state.output:
        await state.output.trace(
            f"[ROUTING] preprocess → {route} (selected_tools: {len(selected_tools) if selected_tools else 0})",
            node="flow",
        )

    return route


async def _route_from_reason(state: State) -> str:
    """Route from reason - act if tools needed, else respond."""
    tool_calls = state.get("tool_calls")
    route = "act" if tool_calls and len(tool_calls) > 0 else "respond"

    if hasattr(state, "output") and state.output:
        await state.output.trace(
            f"[ROUTING] reason → {route} (tool_calls: {len(tool_calls) if tool_calls else 0})",
            node="flow",
        )

    return route


async def _route_from_act(state: State) -> str:
    """Route from act - check iterations and continue research or respond."""
    execution_results = state.get("execution_results", {})
    current_iter = state.get("current_iteration", 0)
    max_iter = state.get("max_iterations", 12)  # Increased default for complex research
    stopping_reason = state.get("stopping_reason")

    # Route back to reason for continued research unless we hit limits
    if stopping_reason in ["max_iterations_reached", "reasoning_loop_detected"]:
        route = "respond"
        reason = stopping_reason
    elif current_iter >= max_iter:
        route = "respond"
        reason = "max_iterations_reached"
        state["stopping_reason"] = reason
    elif not execution_results.success:
        # For failed executions, check if we should retry or give up
        failed_attempts = state.get("failed_tool_attempts", 0)
        if failed_attempts >= 3:  # Give up after 3 consecutive failures
            route = "respond"
            reason = "repeated_tool_failures"
            state["stopping_reason"] = reason
        else:
            route = "reason"
            reason = "execution_failed"
            state["failed_tool_attempts"] = failed_attempts + 1
    else:
        # Success - use quality assessment for routing decisions
        from cogency.nodes.reasoning.adaptive import assess_tools

        tool_quality = assess_tools(execution_results)

        # Route based on quality with max retry protection
        quality_attempts = state.get("quality_retry_attempts", 0)
        max_quality_retries = 2  # Limit quality-based retries

        if tool_quality in ["failed", "poor"] and quality_attempts < max_quality_retries:
            route = "reason"
            reason = f"poor_quality_retry_{quality_attempts + 1}"
            state["quality_retry_attempts"] = quality_attempts + 1
        else:
            # Good quality or max retries reached - continue research
            route = "reason"
            reason = "continue_iteration"
            state["quality_retry_attempts"] = 0  # Reset on good quality

        state["failed_tool_attempts"] = 0  # Reset failure counter on success

    if hasattr(state, "output") and state.output:
        await state.output.trace(
            f"[ROUTING] act → {route} (iter: {current_iter}/{max_iter}, success: {execution_results.success}, reason: {reason})",
            node="flow",
        )

    return route
