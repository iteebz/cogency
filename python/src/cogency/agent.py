from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from cogency.llm import LLM

class AgentState(TypedDict):
    input: str
    output: Optional[str]

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
        res = self.llm.invoke(state["input"])
        return {"output": res}

    def run(self, task: str) -> str:
        init_state = {"input": task, "output": None}
        final_state = self.app.invoke(init_state)
        return final_state["output"]