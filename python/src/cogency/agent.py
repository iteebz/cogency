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
    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        tools: Optional[List[BaseTool]] = None,
        max_depth: int = 10,
    ):
        self.name = name
        self.llm = llm
        self.tools = tools if tools is not None else []
        self.max_depth = max_depth

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
        self.workflow.add_conditional_edges(
            "reason", self._reason_router, {"act": "act", "respond": "respond"}
        )
        self.workflow.add_edge("act", "reflect")
        self.workflow.add_conditional_edges(
            "reflect", self._reflect_router, {"reason": "reason", "respond": "respond"}
        )
        self.workflow.add_edge("respond", END)
        self.app = self.workflow.compile()

    def run(
        self, message: str, enable_trace: bool = False, print_trace: bool = False
    ) -> Dict[str, Any]:
        """Run agent with optional execution trace."""
        # Auto-enable trace if print_trace is requested
        if print_trace:
            enable_trace = True

        context = Context(current_input=message)

        execution_trace = None
        if enable_trace:
            execution_trace = ExecutionTrace(trace_id=str(uuid.uuid4())[:8])
            context.execution_trace = execution_trace

        initial_state: AgentState = {
            "context": context,
            "execution_trace": execution_trace,
        }

        config = {"recursion_limit": self.max_depth}

        if print_trace:
            print("--- Execution Trace ---")
            final_state = None
            for step in self.app.stream(initial_state, config=config):
                # Extract step info for real-time printing
                for node_name, node_state in step.items():
                    if execution_trace and execution_trace.steps:
                        latest_step = execution_trace.steps[-1]
                        if latest_step.node == node_name:
                            from cogency.utils.formatting import (
                                NODE_FORMATTERS,
                                _format_default,
                            )

                            formatter = NODE_FORMATTERS.get(
                                node_name.upper(), _format_default
                            )
                            reasoning = latest_step.reasoning or ""
                            output_data = latest_step.output_data or {}
                            summary = formatter(reasoning, output_data)
                            node_label = f"[{node_name.upper()}]"
                            print(f"{node_label:<10} {summary}")
                final_state = node_state
        else:
            final_state = self.app.invoke(initial_state, config=config)

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

            # Don't double-print trace - it's already printed in real-time

        return result

    def _plan_router(self, state: AgentState) -> str:
        """Direct routing after plan node."""
        last_message = state["context"].messages[-1]["content"]
        # Handle case where content might be a list
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""
        route, _ = parse_plan_response(last_message)
        return route

    def _reason_router(self, state: AgentState) -> str:
        """Route after reason node: to ACT if valid tool call, to RESPOND if not."""
        from cogency.utils.parsing import extract_tool_call

        last_message = state["context"].messages[-1]["content"]
        # Handle case where content might be a list
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""

        tool_call = extract_tool_call(last_message)
        if (
            tool_call and tool_call[0] != "N/A"
        ):  # tool_call is a tuple (tool_name, args)
            return "act"
        else:
            return "respond"

    def _reflect_router(self, state: AgentState) -> str:
        """Direct routing after reflect node."""
        last_message = state["context"].messages[-1]["content"]
        # Handle case where content might be a list
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""
        route, _ = parse_reflect_response(last_message)
        return route
