"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.reasoning.parsing import ReactResponseParser
from cogency.reasoning.adaptive import StoppingReason
from cogency.reasoning.prompts import UNIFIED_REASON
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
            # Route to respond node when reasoning should stop - let respond handle fallback
            state["stopping_reason"] = stopping_reason
            state["next_node"] = NodeNames.RESPOND
            return state
    
    tool_info = ", ".join([f"{t.name}: {t.get_schema()}" for t in selected_tools]) if selected_tools else "no tools"
    
    messages = list(context.messages)
    messages.append({"role": "user", "content": context.current_input})
    
    # Single unified reasoning prompt - handles both initial and reflection
    reasoning_prompt = UNIFIED_REASON.format(
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
    # Reasoning node never provides direct responses - respond node handles ALL responses
    state[StateKeys.DIRECT_RESPONSE] = None
    
    # Determine next node
    if can_answer:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND
    elif state[StateKeys.TOOL_CALLS]:
        state[StateKeys.NEXT_NODE] = NodeNames.ACT
    else:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND  # Fallback to respond if no clear action
    
    return state


