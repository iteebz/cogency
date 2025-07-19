"""Respond node - final response formatting and personality."""
from typing import Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.reasoning.shaper import shape_response
from cogency.messaging import AgentMessenger


def build_response_prompt(system_prompt: Optional[str] = None) -> str:
    """Build response prompt with optional system prompt integration."""
    base_prompt = "Generate final response based on context and tool results.\nBe conversational and helpful. Incorporate all relevant information."
    
    if system_prompt:
        return f"{system_prompt}\n\n{base_prompt}"
    
    return base_prompt


@trace_node("respond")
async def respond_node(state: AgentState, *, llm: BaseLLM, system_prompt: Optional[str] = None, response_shaper: Optional[Dict[str, Any]] = None, config: Optional[Dict] = None) -> AgentState:
    """Respond: generate final formatted response with personality."""
    context = state["context"]
    
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Check if we have a direct response from reasoning OR direct bypass from preprocess
    direct_response = state.get("direct_response")
    direct_bypass = state.get("direct_response_bypass", False)
    
    if direct_bypass:
        # Direct bypass from preprocess - generate response without tools
        final_messages = list(context.messages)
        response_prompt = build_response_prompt(system_prompt)
        final_messages.insert(0, {"role": "system", "content": response_prompt})
        final_response = await llm.invoke(final_messages)
    elif direct_response and system_prompt:
        # Apply system prompt to direct response
        final_messages = list(context.messages)
        response_prompt = build_response_prompt(system_prompt)
        final_messages.insert(0, {"role": "system", "content": response_prompt})
        final_response = await llm.invoke(final_messages)
    elif direct_response:
        # Use direct response as-is
        final_response = direct_response
    else:
        # Generate response based on context and tool results
        final_messages = list(context.messages)
        
        # Context-aware prompt based on execution results
        execution_results = state.get("execution_results", {}).get("results", {})
        if execution_results.get("success"):
            response_prompt = build_response_prompt(system_prompt)
        else:
            response_prompt = "Generate helpful response acknowledging tool failures and providing alternatives."
            if system_prompt:
                response_prompt = f"{system_prompt}\n\n{response_prompt}"
        
        final_messages.insert(0, {"role": "system", "content": response_prompt})
        final_response = await llm.invoke(final_messages)
    
    # Add response to context
    context.add_message("assistant", final_response)
    
    # Apply response shaping if configured
    if response_shaper:
        final_response = await shape_response(final_response, llm, response_shaper)
    
    # Stream final agent response
    if streaming_callback:
        await AgentMessenger.agent_response(streaming_callback, final_response)
    
    # Update state with final results
    state["context"] = context
    state["final_response"] = final_response  # Expected by tests
    state["reasoning_decision"] = ReasoningDecision(
        should_respond=True, 
        response_text=final_response, 
        task_complete=True
    )
    state["last_node_output"] = final_response
    state["next_node"] = "END"
    
    return state