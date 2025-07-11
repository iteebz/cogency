from typing import List, Optional, Any, Dict
from cogency.types import AgentState, ExecutionTrace
from langgraph.graph import StateGraph, END
from cogency.llm import LLM
from cogency.context import Context
from cogency.types import Tool
from cogency.nodes import act, router, respond, plan, reason, reflect
import uuid

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
    
    def run(self, message: str, enable_trace: bool = False) -> Dict[str, Any]:
        """Run agent with optional execution trace."""
        context = Context(current_input=message)
        
        execution_trace = None
        if enable_trace:
            execution_trace = ExecutionTrace(trace_id=str(uuid.uuid4())[:8])
            context.execution_trace = execution_trace
        
        initial_state: AgentState = {
            "context": context,
            "tool_needed": False,
            "task_complete": False,
            "last_node": None,
            "execution_trace": execution_trace
        }
        
        final_state = self.app.invoke(initial_state)
        
        result = {
            "response": final_state["context"].messages[-1]["content"] if final_state["context"].messages else "",
            "conversation": final_state["context"].get_clean_conversation()
        }
        
        if enable_trace and execution_trace:
            result["execution_trace"] = execution_trace.to_dict()
        
        return result