import uuid
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from cogency.context import Context
from cogency.llm import BaseLLM
from cogency.nodes import act, plan, reason, reflect, respond
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ExecutionTrace
from cogency.utils.parsing import parse_plan_response, parse_reflect_response


class Agent:
    def __init__(self, name: str, llm: BaseLLM, tools: Optional[List[BaseTool]] = None):
        self.name = name
        self.llm = llm
        self.tools = tools if tools is not None else []

        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("plan", lambda state: plan(state, self.llm, self.tools))
        self.workflow.add_node(
            "reason", lambda state: reason(state, self.llm, self.tools)
        )
        self.workflow.add_node("act", lambda state: act(state, self.tools))
        self.workflow.add_node("reflect", lambda state: reflect(state, self.llm))
        self.workflow.add_node("respond", lambda state: respond(state, self.llm))

        self.workflow.set_entry_point("plan")

        self.workflow.add_conditional_edges(
            "plan", self._plan_router, {"reason": "reason", "respond": "respond"}
        )
        self.workflow.add_edge("reason", "act")
        self.workflow.add_edge("act", "reflect")
        self.workflow.add_conditional_edges(
            "reflect", self._reflect_router, {"reason": "reason", "respond": "respond"}
        )
        self.workflow.add_edge("respond", END)
        self.app = self.workflow.compile()

    def run(self, message: str, enable_trace: bool = False) -> Dict[str, Any]:
        """Run agent with optional execution trace."""
        context = Context(current_input=message)

        execution_trace = None
        if enable_trace:
            execution_trace = ExecutionTrace(trace_id=str(uuid.uuid4())[:8])
            context.execution_trace = execution_trace

        initial_state: AgentState = {
            "context": context,
            "execution_trace": execution_trace,
        }

        final_state = self.app.invoke(initial_state)

        result = {
            "response": (
                final_state["context"].messages[-1]["content"]
                if final_state["context"].messages
                else "No response generated"
            ),
            "conversation": final_state["context"].get_clean_conversation(),
        }

        if enable_trace and execution_trace:
            result["execution_trace"] = execution_trace.to_dict()

        return result

    def _plan_router(self, state: AgentState) -> str:
        """Direct routing after plan node."""
        last_message = state["context"].messages[-1]["content"]
        route, _ = parse_plan_response(last_message)
        return route

    def _reflect_router(self, state: AgentState) -> str:
        """Direct routing after reflect node."""
        last_message = state["context"].messages[-1]["content"]
        route, _ = parse_reflect_response(last_message)
        return route
