from typing import Any, Dict
from langgraph.graph import END
from cogency.types import AgentState

def router(state: AgentState) -> str:
    
    if state["tool_called"]:
        return "act"
    else:
        return "respond"
