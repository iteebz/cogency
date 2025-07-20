"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, should_respond_directly, extract_reasoning_text
# Eliminated import ceremony - using simple strings
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
5. For calculator operations, do ONE calculation at a time if they depend on each other

Examples:
- "What is 2+2?" → Direct answer (no calculator needed)
- "Weather in Paris?" → Use weather tool, then respond
- "Weather + time in Tokyo?" → Use both tools, then respond immediately
- "Calculate 120*3 + 450" → First use calculator for 120*3, then use result for next calculation

Check: Do I have everything needed to fully answer the ORIGINAL query?
- If YES → {{"reasoning": "I have all needed information", "action": "respond"}}
- If NO → Use specific tools needed

{{"reasoning": "Explain your thinking in 1-2 sentences", "action": "respond"}}
OR
{{"reasoning": "Why you need these tools", "action": "use_tools", "tool_calls": [{{"name": "tool_name", "args": {{"param": "value"}}}}]}}"""




@trace_node("reason")
async def reason_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], system_prompt: Optional[str] = None, config: Optional[Dict] = None) -> AgentState:
    """Reason: analyze context and decide next action (includes implicit reflection)."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Simple iteration tracking
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    
    if current_iteration >= max_iterations:
        # Stop reasoning after max iterations
        state["stopping_reason"] = "max_iterations_reached"
        state["next_node"] = "respond"
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
    
    try:
        llm_response = await llm.invoke(messages)
        context.add_message("assistant", llm_response)
        
        # Parse response using consolidated utilities
        json_data = extract_json_from_response(llm_response)
        can_answer = should_respond_directly(json_data)
        tool_calls = extract_tool_calls_from_json(json_data)
    except Exception as e:
        # Handle LLM or parsing errors gracefully
        error_msg = f"Reasoning failed: {str(e)}"
        context.add_message("system", error_msg)
        # Default to responding directly when reasoning fails
        can_answer = True
        tool_calls = None
        llm_response = "I encountered an issue with reasoning, but I'll do my best to help you."
    
    # Extract intelligent reasoning text and stream it - HUMAN READABLE ONLY
    reasoning_text = extract_reasoning_text(llm_response)
    if streaming_callback:
        await AgentMessenger.reason(streaming_callback, reasoning_text)
    
    # Store reasoning results in state - NO JSON LEAKAGE
    state["reasoning_response"] = llm_response
    state["can_answer_directly"] = can_answer
    state["tool_calls"] = tool_calls
    # Reasoning node never provides direct responses - respond node handles ALL responses
    state["direct_response"] = None
    
    # Increment iteration counter
    state["current_iteration"] = current_iteration + 1
    
    # Determine next node
    if can_answer:
        state["next_node"] = "respond"
    elif tool_calls:
        state["next_node"] = "act"
    else:
        state["next_node"] = "respond"  # Fallback to respond if no clear action
    
    return state


