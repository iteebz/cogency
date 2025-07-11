from typing import List, Optional, Any, Dict
from cogency.types import AgentState
from langgraph.graph import StateGraph, END
from cogency.llm import LLM
from cogency.context import Context
from cogency.types import Tool
from cogency.nodes import llm_response, act, router, respond

class Agent:
    def __init__(self, name: str, llm: LLM, tools: Optional[List[Tool]] = None):
        self.name = name
        self.llm = llm
        self.tools = tools if tools is not None else []

        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("llm_response", lambda state: invoke_llm(state, self.llm, self.tools))
        self.workflow.add_node("act", lambda state: act(state, self.tools))
        self.workflow.add_node("respond", lambda state: respond(state, self.llm))

        self.workflow.set_entry_point("llm_response")
        self.workflow.add_edge("llm_response", "act")
        self.workflow.add_conditional_edges(
            "act",
            router,
            {"act": "llm_response", "respond": "respond"}
        )
        self.workflow.add_edge("respond", END)
        self.app = self.workflow.compile()

    def run(self, context: Context) -> Context:
        init_state = {"context": context}
        final_state = self.app.invoke(init_state)
        return final_state["context"]