from typing import TypedDict
from langgraph.graph import StateGraph, END
from cogency.llm import LLM
from cogency.context import Context

class AgentState(TypedDict):
    context: Context

class Agent:
    def __init__(self, name: str, llm: LLM):
        self.name = name
        self.llm = llm

        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("llm_response", self._llm_response_node)
        self.workflow.set_entry_point("llm_response")
        self.workflow.add_edge("llm_response", END)
        self.app = self.workflow.compile()

    def _llm_response_node(self, state: AgentState) -> AgentState:
        context = state["context"]
        res = self.llm.invoke(context.messages)
        context.add_message("assistant", res)
        return {"context": context}

    def run(self, context: Context) -> Context:
        init_state = {"context": context}
        final_state = self.app.invoke(init_state)
        return final_state["context"]