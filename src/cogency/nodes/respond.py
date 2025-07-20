"""Respond node - final response formatting and personality."""
from typing import Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.response.core import shape_response
from cogency.messaging import AgentMessenger


def build_response_prompt(system_prompt: Optional[str] = None, has_tool_results: bool = False) -> str:
    """Build response prompt with optional system prompt integration."""
    if has_tool_results:
        base_prompt = "Generate final response based on context and tool results.\nBe conversational and helpful. Incorporate all relevant information."
    else:
        base_prompt = "Answer the user's question directly and conversationally using your knowledge."
    
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
    
    # ALWAYS generate response - handle tool results, direct reasoning, or knowledge-based
    final_messages = list(context.messages)
    
    # Check for stopping reason
    stopping_reason = state.get("stopping_reason")
    
    if stopping_reason:
        # Handle reasoning stopped scenario - generate fallback response
        fallback_prompt = f"Reasoning stopped due to: {stopping_reason}. Please summarize the conversation and provide a helpful response based on the context available."
        if system_prompt:
            fallback_prompt = f"{system_prompt}\n\n{fallback_prompt}"
        
        final_messages.insert(0, {"role": "system", "content": fallback_prompt})
        final_response = await llm.invoke(final_messages)
    else:
        # Generate response based on context and any tool results
        execution_results = state.get("execution_results", {})
        if execution_results and execution_results.get("success"):
            response_prompt = build_response_prompt(system_prompt, has_tool_results=True)
        elif execution_results and not execution_results.get("success"):
            response_prompt = "Generate helpful response acknowledging tool failures and providing alternatives."
            if system_prompt:
                response_prompt = f"{system_prompt}\n\n{response_prompt}"
        else:
            # No tool results - answer with knowledge or based on conversation
            response_prompt = build_response_prompt(system_prompt, has_tool_results=False)
        
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