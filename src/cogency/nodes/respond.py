import json
from typing import Dict, Any, Optional, List
from cogency.tools.base import BaseTool
from cogency.llm import BaseLLM
from cogency.types import AgentState
from cogency.utils import trace

RESPOND_PROMPT = """
You are an AI assistant providing the final response to the user.

RESPONSE TASK:
Generate a clear, helpful, and conversational response based on the entire
conversation history and tool outputs.

RESPONSE RULES:
1. Be conversational and natural - speak directly to the user
2. Incorporate tool results seamlessly into your response
3. NEVER include technical syntax like TOOL_CALL: or internal JSON
4. If tools provided data, present it clearly and explain its relevance
5. If errors occurred, explain them in user-friendly terms
6. Keep responses concise but complete

TONE: Professional, helpful, and direct. Answer as if you're speaking to a colleague.
"""


@trace
async def respond(state: AgentState, *, llm: BaseLLM, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Respond node generates final response."""
    
    context = state["context"]

    # Check if the last message is a direct response JSON
    last_message = context.messages[-1]["content"]

    # Handle case where content might be a list
    if isinstance(last_message, list):
        last_message = last_message[0] if last_message else ""

    try:
        data = json.loads(last_message)
        if data.get("action") == "direct_response":
            # Replace the JSON with the clean answer
            clean_answer = data.get("answer", last_message)
            context.messages[-1]["content"] = clean_answer
            
            return {"context": context, "execution_trace": state["execution_trace"]}
    except (json.JSONDecodeError, TypeError):
        pass

    # For non-direct responses, use the LLM to generate a response
    messages = list(context.messages)
    
    # Use prompt fragments if provided, otherwise use default
    if prompt_fragments and "aip_format" in prompt_fragments:
        system_prompt = RESPOND_PROMPT + "\n\n" + prompt_fragments["aip_format"]
    else:
        system_prompt = RESPOND_PROMPT
    
    messages.insert(0, {"role": "system", "content": system_prompt})

    # Get the final response
    llm_response = await llm.invoke(messages)

    # Replace the last message with the clean response
    context.messages[-1]["content"] = llm_response

    # Return updated state
    return {"context": context, "execution_trace": state["execution_trace"]}
