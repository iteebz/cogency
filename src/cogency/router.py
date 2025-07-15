from typing import Dict, List, Any, Optional
from cogency.types import AgentState, ExecutionTrace
from cogency.utils import parse_plan, parse_reflect
from cogency.tools.base import BaseTool
from cogency.constants import NodeName


class Router:
    """Encapsulates routing logic for the cognitive workflow."""

    def __init__(self, tools: List[BaseTool]):
        self.tools = tools

    def route(self, state: AgentState) -> str:
        """Determines the next node based on the current agent state."""
        trace: ExecutionTrace = state["trace"]
        last_node_output: Optional[Any] = state.get("last_node_output")

        # Routing from 'think' node
        if state.get("thinking_response"):
            if state.get("skip_thinking"):
                trace.add("router", f"Routing from {NodeName.THINK.value.upper()}: skip_thinking is true, going to {NodeName.RESPOND.value.upper()}")
                return NodeName.RESPOND.value
            
            thinking_decision = state["thinking_response"].get("decision")
            if thinking_decision == "need_tools":
                trace.add("router", f"Routing from {NodeName.THINK.value.upper()}: thinking output indicates tools needed, going to {NodeName.PLAN.value.upper()}")
                return NodeName.PLAN.value
            elif thinking_decision == "direct_response":
                trace.add("router", f"Routing from {NodeName.THINK.value.upper()}: no tools needed, going to {NodeName.RESPOND.value.upper()}")
                return NodeName.RESPOND.value
            else:
                trace.add("router", f"Warning: Thinking decision not recognized, defaulting to {NodeName.RESPOND.value.upper()}", {"thinking_response": state["thinking_response"]})
                return NodeName.RESPOND.value

        # Routing from 'plan' or 'reflect' nodes
        plan_data = parse_plan(last_node_output)
        if plan_data:
            action = plan_data.get("action")
            if action == "tool_needed":
                trace.add("router", f"Routing from {NodeName.PLAN.value.upper()}: plan indicates tool needed, going to {NodeName.ACT.value.upper()}")
                return NodeName.ACT.value
            elif action == "direct_response":
                trace.add("router", f"Routing from {NodeName.PLAN.value.upper()}: plan indicates direct response, going to {NodeName.RESPOND.value.upper()}")
                return NodeName.RESPOND.value
            else:
                trace.add("router", f"Warning: Plan parsing failed or action not recognized, defaulting to {NodeName.RESPOND.value.upper()}", {"plan_data": plan_data})
                return NodeName.RESPOND.value

        reflect_data = parse_reflect(last_node_output)
        if reflect_data:
            status = reflect_data.get("status")
            if status == "continue":
                trace.add("router", f"Routing from {NodeName.REFLECT.value.upper()}: reflection indicates continue, going to {NodeName.PLAN.value.upper()}")
                return NodeName.PLAN.value
            elif status == "complete":
                trace.add("router", f"Routing from {NodeName.REFLECT.value.upper()}: reflection indicates complete, going to {NodeName.RESPOND.value.upper()}")
                return NodeName.RESPOND.value
            else:
                trace.add("router", f"Warning: Reflect parsing failed or status not recognized, defaulting to {NodeName.RESPOND.value.upper()}", {"reflect_data": reflect_data})
                return NodeName.RESPOND.value

        trace.add("router", f"Routing: default fallback to {NodeName.RESPOND.value.upper()}")
        return NodeName.RESPOND.value
