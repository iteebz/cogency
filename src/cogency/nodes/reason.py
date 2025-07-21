"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.tracing import trace_node
from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, extract_reasoning_text
# Eliminated import ceremony - using simple strings
from cogency.messaging import AgentMessenger


# REASON PROMPT - Clearly visible at top for easy scanning and modification
REASON_PROMPT = """Analyze the conversation and decide your next action.

ORIGINAL QUERY: {user_input}
AVAILABLE TOOLS: {tool_names}

CRITICAL RULES:
1. If the user asks you to CREATE, RUN, EXECUTE, or SAVE anything - you MUST use tools
2. If the user wants files created or code executed - you MUST use appropriate tools
3. Only respond directly if the user asks for explanations or information you already know
4. FOLLOW TOOL SCHEMAS EXACTLY - include all required parameters
5. Do not add extra steps or features not requested by the user

Action Required Analysis:
- Does the query ask to CREATE/SAVE files? → Use file tool
- Does the query ask to RUN/EXECUTE code? → Use appropriate execution tool  
- Does the query ask for explanation only? → Respond directly

RESPONSE FORMAT - YOU MUST OUTPUT EXACTLY THIS JSON FORMAT:

For CREATE/RUN/EXECUTE requests (like the current query):
{{"reasoning": "I need to create a Python script and run it", "tool_calls": [{{"name": "code", "args": {{"code": "def fibonacci(n): return n", "language": "python"}}}}]}}

For information-only requests:
{{"reasoning": "I have all needed information to explain this topic"}}

CRITICAL: Output ONLY the JSON object. No explanations, no code blocks, no markdown."""




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
    
    if selected_tools:
        tool_info_parts = []
        for t in selected_tools:
            schema = t.get_schema()
            examples = getattr(t, 'get_usage_examples', lambda: [])()
            if examples:
                example_str = " Examples: " + ", ".join(examples[:2])  # Show first 2 examples
                tool_info_parts.append(f"{t.name}: {schema}.{example_str}")
            else:
                tool_info_parts.append(f"{t.name}: {schema}")
        tool_info = "\n".join(tool_info_parts)
    else:
        tool_info = "no tools"
    
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
        llm_response = await llm.run(messages)
        context.add_message("assistant", llm_response)
        
        # Parse response using consolidated utilities
        json_data = extract_json_from_response(llm_response)
        tool_calls = extract_tool_calls_from_json(json_data)
        # Direct response is implicit when no tool_calls
        can_answer = tool_calls is None or len(tool_calls) == 0
    except Exception as e:
        # Handle LLM or parsing errors gracefully
        error_msg = f"I encountered an issue while thinking through your request: {str(e)}"
        context.add_message("system", error_msg)
        # Default to responding directly when reasoning fails
        can_answer = True
        tool_calls = None
        llm_response = "I encountered an issue with reasoning, but I'll do my best to help you."
    
    # Extract intelligent reasoning text and stream it - HUMAN READABLE ONLY
    reasoning_text = extract_reasoning_text(llm_response)
    if streaming_callback:
        await AgentMessenger.reasoning(streaming_callback, reasoning_text)
    
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


