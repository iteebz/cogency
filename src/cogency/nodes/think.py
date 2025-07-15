"""Deep thinking node for complex queries."""
import json
from typing import Dict, Any, Optional
from cogency.llm import BaseLLM
from cogency.types import AgentState
from cogency.utils.trace import trace_node

THINK_PROMPT = """Analyze: "{user_input}"

Key question: Can I answer directly or need tools?

Brief reasoning:
- Core request: 
- Complexity level:
- Tools needed: [Y/N]

Your output MUST be valid JSON:
{{"decision": "direct_response", "reasoning": "<reason>"}} OR
{{"decision": "need_tools", "reasoning": "<reason>", "tools": "<specific tools needed>"}}"""


@trace_node("think")
async def think(state: AgentState, llm: BaseLLM, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Think node performs deep reasoning."""
    
    context = state["context"]
    user_input = context.current_input
    
    # Prepare messages for thinking
    messages = context.messages + [{"role": "user", "content": context.current_input}]
    
    system_prompt = THINK_PROMPT.format(
        user_input=user_input,
        injection_point=prompt_fragments.get("injection_point", "") if prompt_fragments else ""
    )
    messages.insert(0, {"role": "system", "content": system_prompt})
    
    # Get thinking response
    llm_response = await llm.invoke(messages)
    
    try:
        thinking_response_parsed = json.loads(llm_response)
    except json.JSONDecodeError:
        thinking_response_parsed = {"decision": "direct_response", "reasoning": "Malformed JSON from LLM, defaulting to direct response."}

    # Store thinking in context for downstream nodes
    context.add_message("assistant", f"[THINKING] {llm_response}")
    
    # Return updated state
    return {"context": context, "thinking_response": thinking_response_parsed, "last_node_output": llm_response}