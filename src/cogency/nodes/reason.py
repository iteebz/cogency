"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.reasoning.parsing import ReactResponseParser
from cogency.reasoning.adaptive import StoppingReason
from cogency.reasoning.prompts import ReasoningPrompts
from cogency.constants import NodeNames, StateKeys
from cogency.messaging import AgentMessenger




@trace_node("reason")
async def reason_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], system_prompt: Optional[str] = None, config: Optional[Dict] = None) -> AgentState:
    """Reason: analyze context and decide next action (includes implicit reflection)."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    controller = state.get("adaptive_controller")
    
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Check adaptive reasoning limits if controller exists
    if controller:
        should_continue, stopping_reason = controller.should_continue_reasoning()
        if not should_continue:
            # Generate fallback response when reasoning should stop
            return await _generate_fallback_response(state, llm, stopping_reason, system_prompt)
    
    tool_info = ", ".join([f"{t.name}: {t.get_schema()}" for t in selected_tools]) if selected_tools else "no tools"
    
    messages = list(context.messages)
    messages.append({"role": "user", "content": context.current_input})
    
    # Determine if this is initial reasoning or reflection on tool results
    has_tool_results = state.get("execution_results") is not None
    
    # Choose appropriate prompt based on context
    if has_tool_results:
        # This is reflection after tool execution
        reasoning_prompt = ReasoningPrompts.REFLECTION.format(
            tool_names=tool_info,
            user_input=context.current_input
        )
    else:
        # This is initial reasoning
        reasoning_prompt = ReasoningPrompts.INITIAL_REASON.format(
            tool_names=tool_info,
            user_input=context.current_input
        )
    
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"
    
    messages.insert(0, {"role": "system", "content": reasoning_prompt})
    
    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)
    
    parser = ReactResponseParser()
    can_answer = parser.can_answer_directly(llm_response)
    
    # Extract intelligent reasoning text and stream it
    reasoning_text = parser.extract_reasoning(llm_response)
    if streaming_callback:
        await AgentMessenger.reason(streaming_callback, reasoning_text)
    
    # Store reasoning results in state
    state[StateKeys.REASONING_RESPONSE] = llm_response
    state[StateKeys.CAN_ANSWER_DIRECTLY] = can_answer
    state[StateKeys.TOOL_CALLS] = parser.extract_tool_calls(llm_response)
    state[StateKeys.DIRECT_RESPONSE] = parser.extract_answer(llm_response) if can_answer else None
    
    # Determine next node
    if can_answer:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND
    elif state[StateKeys.TOOL_CALLS]:
        state[StateKeys.NEXT_NODE] = NodeNames.ACT
    else:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND  # Fallback to respond if no clear action
    
    return state


async def _generate_fallback_response(state: AgentState, llm: BaseLLM, stopping_reason: StoppingReason, system_prompt: Optional[str] = None) -> AgentState:
    """Generate fallback response when reasoning loop should stop."""
    context = state["context"]
    
    # Generate a proper summary based on tool results in context
    summary_prompt = ReasoningPrompts.FALLBACK_SUMMARY.format(
        stopping_reason=stopping_reason
    )
    
    final_messages = list(context.messages)
    final_messages.append({"role": "user", "content": summary_prompt})
    
    if system_prompt:
        summary_prompt = f"{system_prompt}\n\n{summary_prompt}"
    
    final_messages.insert(0, {"role": "system", "content": ReasoningPrompts.FALLBACK_SYSTEM})
    
    final_response = await llm.invoke(final_messages)
    context.add_message("assistant", final_response)
    
    # Set state for respond node
    state[StateKeys.CONTEXT] = context
    state["reasoning_decision"] = ReasoningDecision(
        should_respond=True, 
        response_text=final_response, 
        task_complete=True
    )
    state["last_node_output"] = final_response
    state[StateKeys.DIRECT_RESPONSE] = final_response
    state[StateKeys.NEXT_NODE] = NodeNames.RESPOND
    
    return state