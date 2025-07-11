from typing import Any, Dict
from langgraph.graph import END
from cogency.types import AgentState

def router(state: AgentState) -> str:
    last_node = state.get("last_node")

    if last_node == "plan":
        if state["tool_needed"]:
            return "tool_needed"
        else:
            return "direct_response"
    elif last_node == "reflect":
        if state["task_complete"]:
            return "task_complete"
        else:
            return "continue_task"
    return "error"