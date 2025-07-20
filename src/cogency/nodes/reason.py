"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, should_respond_directly, extract_reasoning_text
from cogency.reasoning.adaptive import StoppingReason
from cogency.constants import NodeNames, StateKeys
from cogency.messaging import AgentMessenger


# REASON PROMPT - Clearly visible at top for easy scanning and modification
REASON_PROMPT = """Analyze the conversation and decide your next action.

ORIGINAL QUERY: {user_input}
AVAILABLE TOOLS: {tool_names}

CRITICAL RULES:
1. Only use tools for current/external data that you cannot know
2. Once you have ALL information needed to answer the original query, respond immediately
3. Do not add extra steps or features not requested by the user
4. Review what the user actually asked for vs what you have gathered

Examples:
- "What is 2+2?" → Direct answer (no calculator needed)
- "Weather in Paris?" → Use weather tool, then respond
- "Weather + time in Tokyo?" → Use both tools, then respond immediately

Check: Do I have everything needed to fully answer the ORIGINAL query?
- If YES → {{"reasoning": "I have all needed information", "action": "respond"}}
- If NO → Use specific tools needed

{{"reasoning": "Explain your thinking in 1-2 sentences", "action": "respond"}}
OR
{{"reasoning": "Why you need this tool", "action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
OR  
{{"reasoning": "Why you need these tools", "action": "use_tools", "tool_call": {{"calls": [...]}}}}"""




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
    reasoning_prompt = REASON_PROMPT.format(
        tool_names=tool_info,
        user_input=context.current_input
    )
    
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"
    
    messages.insert(0, {"role": "system", "content": reasoning_prompt})
    
    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)
    
    # Parse response using consolidated utilities
    json_data = extract_json_from_response(llm_response)
    can_answer = should_respond_directly(json_data)
    tool_calls = extract_tool_calls_from_json(json_data)
    
    # Extract intelligent reasoning text and stream it - HUMAN READABLE ONLY
    reasoning_text = extract_reasoning_text(llm_response)
    if streaming_callback:
        await AgentMessenger.reason(streaming_callback, reasoning_text)
    
    # Store reasoning results in state - NO JSON LEAKAGE
    state[StateKeys.REASONING_RESPONSE] = llm_response
    state[StateKeys.CAN_ANSWER_DIRECTLY] = can_answer
    state[StateKeys.TOOL_CALLS] = tool_calls
    # Reasoning node never provides direct responses - respond node handles ALL responses
    state[StateKeys.DIRECT_RESPONSE] = None
    
    # Determine next node
    if can_answer:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND
    elif tool_calls:
        state[StateKeys.NEXT_NODE] = NodeNames.ACT
    else:
        state[StateKeys.NEXT_NODE] = NodeNames.RESPOND  # Fallback to respond if no clear action
    
    return state


