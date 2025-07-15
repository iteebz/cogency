from typing import Dict, List, Any, Optional
from cogency.types import AgentState, ExecutionTrace, ReasoningDecision
from cogency.tools.base import BaseTool
from cogency.constants import NodeName


class Router:
    """Simplified routing logic - NO JSON PARSING CEREMONY."""

    def __init__(self, tools: List[BaseTool]):
        self.tools = tools

    def route(self, state: AgentState) -> str:
        """Determines the next node based on structured decision types."""
        trace: ExecutionTrace = state["trace"]
        
        # Check for ReasoningDecision from new reason node
        reasoning_decision = state.get("reasoning_decision")
        if reasoning_decision and isinstance(reasoning_decision, ReasoningDecision):
            if reasoning_decision.task_complete:
                trace.add("router", "REASON node completed task, ending workflow")
                return NodeName.RESPOND.value
            else:
                trace.add("router", "REASON node continuing workflow")
                return NodeName.REASON.value
        
        # Default fallback
        trace.add("router", "Default fallback to RESPOND")
        return NodeName.RESPOND.value
