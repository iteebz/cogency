from typing import Dict, Any, Optional
from cogency.llm import BaseLLM
from cogency.types import AgentState, ReasoningDecision
from cogency.utils.trace import trace_node


@trace_node("respond")
async def respond(state: AgentState, *, llm: BaseLLM, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Respond node - simplified to just extract final response."""
    
    context = state["context"]
    
    # Check if we have a ReasoningDecision with response_text
    reasoning_decision = state.get("reasoning_decision")
    if reasoning_decision and isinstance(reasoning_decision, ReasoningDecision):
        if reasoning_decision.response_text:
            # Use the response from reasoning
            return {"context": context, "response": reasoning_decision.response_text}
    
    # Fallback: get the last assistant message as response
    last_message = context.messages[-1]["content"] if context.messages else "No response generated"
    
    return {"context": context, "response": last_message}