from typing import List, Optional, Any, Dict
from cogency.types import AgentState
from langgraph.graph import StateGraph, END
from cogency.llm import LLM
from cogency.context import Context
from cogency.types import Tool
from cogency.nodes import act, router, respond, plan, reason, reflect

class Agent:
    def __init__(self, name: str, llm: LLM, tools: Optional[List[Tool]] = None):
        self.name = name
        self.llm = llm
        self.tools = tools if tools is not None else []

        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("plan", lambda state: plan(state, self.llm, self.tools))
        self.workflow.add_node("reason", lambda state: reason(state, self.llm, self.tools))
        self.workflow.add_node("act", lambda state: act(state, self.tools))
        self.workflow.add_node("reflect", lambda state: reflect(state, self.llm))
        self.workflow.add_node("respond", lambda state: respond(state, self.llm))

        self.workflow.set_entry_point("plan")

        self.workflow.add_conditional_edges(
            "plan",
            router,
            {"tool_needed": "reason", "direct_response": "respond"}
        )
        self.workflow.add_edge("reason", "act")
        self.workflow.add_edge("act", "reflect") # New edge: act -> reflect
        self.workflow.add_conditional_edges(
            "reflect",
            router,
            {"task_complete": "respond", "continue_task": "reason"} # New routing from reflect
        )
        self.workflow.add_edge("respond", END)
        self.app = self.workflow.compile()