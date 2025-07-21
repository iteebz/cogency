"""Respond node - final response formatting and personality."""
from typing import Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.state import State
# ReasoningDecision removed - was bullshit that didn't align with adaptive reasoning



def build_prompt(system_prompt: Optional[str] = None, has_tool_results: bool = False, identity: Optional[str] = None, json_schema: Optional[str] = None) -> str:
    """Build clean system prompt with identity and optional JSON schema."""
    if has_tool_results:
        base_prompt = "Generate final response based on context and tool results.\nBe conversational and helpful. Incorporate all relevant information."
    else:
        base_prompt = "Answer the user's question directly and conversationally using your knowledge."
    
    # Simple identity
    if identity:
        base_prompt = f"You are {identity}. {base_prompt}"
    
    # JSON schema if provided
    if json_schema:
        base_prompt += f"\n\nRespond with valid JSON matching this schema:\n{json_schema}"
    
    if system_prompt:
        return f"{system_prompt}\n\n{base_prompt}"
    
    return base_prompt




async def respond(state: State, *, llm: BaseLLM, system_prompt: Optional[str] = None, identity: Optional[str] = None, json_schema: Optional[str] = None, config: Optional[Dict] = None) -> State:
    """Respond: generate final formatted response with personality."""
    context = state["context"]
    
    # Streaming handled by Output
    
    # ALWAYS generate response - handle tool results, direct reasoning, or knowledge-based
    final_messages = list(context.messages)
    
    # Check for stopping reason
    stopping_reason = state.get("stopping_reason")
    
    if stopping_reason:
        # Handle reasoning stopped scenario - generate fallback response
        await state.output.send("trace", f"Fallback response due to: {stopping_reason}", node="respond")
        fallback_prompt = f"Reasoning stopped due to: {stopping_reason}. Please summarize the conversation and provide a helpful response based on the context available."
        if system_prompt:
            fallback_prompt = f"{system_prompt}\n\n{fallback_prompt}"
        
        final_messages.insert(0, {"role": "system", "content": fallback_prompt})
        try:
            # Stream the fallback response
            final_response = ""
            async for chunk in llm.stream(final_messages):
                final_response += chunk
                await state.output.send("update", chunk)
        except Exception as e:
            # Handle LLM errors in fallback response generation
            final_response = f"I apologize, but I encountered a technical issue while preparing my response: {str(e)}. Let me try to help based on what we discussed."
            await state.output.send("update", final_response)
    else:
        # Generate response based on context and any tool results
        execution_results = state.get("execution_results", {})
        if execution_results and execution_results.get("success"):
            if json_schema:
                await state.output.send("trace", "Applying JSON schema constraint", node="respond")
            response_prompt = build_prompt(system_prompt, has_tool_results=True, identity=identity, json_schema=json_schema)
        elif execution_results and not execution_results.get("success"):
            response_prompt = "Generate helpful response acknowledging tool failures and providing alternatives."
            if system_prompt:
                response_prompt = f"{system_prompt}\n\n{response_prompt}"
        else:
            # No tool results - answer with knowledge or based on conversation
            response_prompt = build_prompt(system_prompt, has_log_tools=False, identity=identity, json_schema=json_schema)
        
        final_messages.insert(0, {"role": "system", "content": response_prompt})
        try:
            # Stream the main response
            final_response = ""
            async for chunk in llm.stream(final_messages):
                final_response += chunk
                await state.output.send("update", chunk)
        except Exception as e:
            # Handle LLM errors in response generation
            final_response = f"I apologize, but I encountered a technical issue while generating my response: {str(e)}. Please try again."
            await state.output.send("update", final_response)
    
    # Add response to context
    context.add_message("assistant", final_response)
    
    # Update flow state
    state["final_response"] = final_response
    
    # Store response data directly in state
    state["reasoning_decision"] = {
        "should_respond": True, 
        "response_text": final_response, 
        "task_complete": True
    }
    state["last_node_output"] = final_response
    state["next_node"] = "END"
    
    return state