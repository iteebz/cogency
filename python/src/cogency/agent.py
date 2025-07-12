import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from langgraph.graph import END, StateGraph

from cogency.context import Context
from cogency.embed import BaseEmbed
from cogency.llm import BaseLLM
from cogency.nodes import act, plan, reason, reflect, respond
from cogency.nodes.plan import plan_streaming
from cogency.nodes.reason import reason_streaming
from cogency.nodes.act import act_streaming
from cogency.nodes.reflect import reflect_streaming
from cogency.nodes.respond import respond_streaming
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ExecutionTrace
from cogency.utils.interrupt import interruptable
from cogency.utils.parsing import parse_plan_response, parse_reflect_response


class Agent:
    """
    Cogency Agent with stream-first architecture.
    
    Features revolutionary streaming where agents are defined by their streams,
    not just made streamable. Every node is an async generator that yields
    thinking steps in real-time.
    
    Args:
        name: Agent identifier
        llm: Language model instance supporting streaming
        tools: Optional list of tools for agent to use
        embed: Optional embedding model for retrieval
        max_depth: Maximum reasoning depth
    """
    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        tools: Optional[List[BaseTool]] = None,
        embed: Optional[BaseEmbed] = None,
        max_depth: int = 10,
    ):
        self.name = name
        self.llm = llm
        self.tools = tools if tools is not None else []
        self.embed = embed
        self.max_depth = max_depth

        self.workflow = StateGraph(AgentState)

        async def plan_node(state):
            return await plan(state, self.llm, self.tools)

        async def reason_node(state):
            return await reason(state, self.llm, self.tools)

        async def act_node(state):
            return await act(state, self.tools)

        async def reflect_node(state):
            return await reflect(state, self.llm)

        async def respond_node(state):
            return await respond(state, self.llm)

        self.workflow.add_node("plan", plan_node)
        self.workflow.add_node("reason", reason_node)
        self.workflow.add_node("act", act_node)
        self.workflow.add_node("reflect", reflect_node)
        self.workflow.add_node("respond", respond_node)

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

    @property
    def context(self) -> Optional[Context]:
        """Get the current context if available."""
        return getattr(self, "_context", None)

    @interruptable
    async def run(
        self,
        message: str,
        enable_trace: bool = False,
        print_trace: bool = False,
        context: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Run agent with optional execution trace."""
        # Auto-enable trace if print_trace is requested
        if print_trace:
            enable_trace = True

        # Use provided context or create new one
        if context is None:
            context = Context(current_input=message)
        else:
            context.current_input = message

        # Store context for property access
        self._context = context

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
            async for step in self.app.astream(initial_state, config=config):
                # Extract step info for real-time printing
                for node_name, node_state in step.items():
                    if execution_trace and execution_trace.steps:
                        latest_step = execution_trace.steps[-1]
                        if latest_step.node == node_name:
                            from cogency.utils.formatting import (
                                NODE_FORMATTERS,
                                _format_default,
                            )

                            formatter = NODE_FORMATTERS.get(node_name.upper(), _format_default)
                            reasoning = latest_step.reasoning or ""
                            output_data = latest_step.output_data or {}
                            summary = formatter(reasoning, output_data)
                            node_label = f"[{node_name.upper()}]"
                            print(f"{node_label:<10} {summary}")
                final_state = node_state
        else:
            final_state = await self.app.ainvoke(initial_state, config=config)

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

    async def stream(self, message: str, context: Optional[Context] = None, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
        """Stream the agent's execution process in real-time.
        
        Revolutionary streaming architecture where the stream IS the execution,
        not a view of it. Every node yields thinking steps as they happen.
        
        Args:
            message: User input message
            context: Optional context to continue conversation
            yield_interval: Minimum time between yields for rate limiting (seconds)
            
        Yields:
            Dict[str, Any]: Streaming chunks with types:
                - thinking: Agent's reasoning process
                - chunk: LLM response chunks
                - result: Node execution results
                - tool_call: Tool execution events
                - error: Error events
                - state: Updated agent state
        """
        # Use provided context or create new one
        if context is None:
            context = Context(current_input=message)
        else:
            context.current_input = message

        # Store context for property access
        self._context = context

        initial_state: AgentState = {
            "context": context,
            "execution_trace": None,
        }

        # Stream through complete agent workflow: plan → reason → act → reflect → respond
        current_state = initial_state
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 1. Plan Phase
            async for chunk in plan_streaming(current_state, self.llm, self.tools, yield_interval):
                yield chunk
                if chunk["type"] == "state":
                    current_state = chunk["state"]
            
            # Check plan decision
            plan_decision = self._plan_router(current_state)
            
            if plan_decision == "respond":
                # Direct response - go straight to respond
                async for chunk in respond_streaming(current_state, self.llm, yield_interval):
                    yield chunk
                    if chunk["type"] == "state":
                        current_state = chunk["state"]
                break
            
            elif plan_decision == "reason":
                # 2. Reason Phase
                async for chunk in reason_streaming(current_state, self.llm, self.tools, yield_interval):
                    yield chunk
                    if chunk["type"] == "state":
                        current_state = chunk["state"]
                
                # 3. Act Phase
                async for chunk in act_streaming(current_state, self.tools, yield_interval):
                    yield chunk
                    if chunk["type"] == "state":
                        current_state = chunk["state"]
                
                # 4. Reflect Phase
                async for chunk in reflect_streaming(current_state, self.llm, yield_interval):
                    yield chunk
                    if chunk["type"] == "state":
                        current_state = chunk["state"]
                
                # Check reflection decision
                reflect_decision = self._reflect_router(current_state)
                
                if reflect_decision == "respond":
                    # 5. Respond Phase
                    async for chunk in respond_streaming(current_state, self.llm, yield_interval):
                        yield chunk
                        if chunk["type"] == "state":
                            current_state = chunk["state"]
                    break
                # If continue, loop back to plan
            
            else:
                # Unknown decision, break
                yield {"type": "error", "node": "agent", "content": f"Unknown plan decision: {plan_decision}"}
                break

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
        if tool_call and tool_call[0] != "N/A":  # tool_call is a tuple (tool_name, args)
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
