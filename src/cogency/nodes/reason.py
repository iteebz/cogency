"""Reason node - pure reasoning and decision making."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.tracing import trace_node
from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, extract_reasoning_text
from cogency.messaging import AgentMessenger
from cogency.nodes.reasoning import (
    initialize_cognitive_state,
    update_cognitive_state,
    create_action_fingerprint,
    detect_action_loop,
    assess_tool_quality,
    create_attempts_summary,
    track_failed_attempt,
    REASON_PROMPT
)




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
    
    # Initialize cognitive state
    cognitive_state = initialize_cognitive_state(state)
    
    # Enhanced loop detection (with graceful fallback)
    try:
        loop_detected = detect_action_loop(cognitive_state)
    except Exception:
        loop_detected = False  # Fallback to no loop detection if it fails
    
    if current_iteration >= max_iterations:
        # Stop reasoning after max iterations
        state["stopping_reason"] = "max_iterations_reached"
        state["next_node"] = "respond"
        return state
    elif loop_detected:
        # Stop reasoning if loop detected
        state["stopping_reason"] = "reasoning_loop_detected"
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
    
    # Create attempts summary from failed attempts
    failed_attempts = cognitive_state.get("failed_attempts", [])
    attempts_summary = create_attempts_summary(failed_attempts)
    
    # Enhanced reasoning prompt with cognitive context (graceful degradation)
    try:
        reasoning_prompt = REASON_PROMPT.format(
            tool_names=tool_info,
            user_input=context.current_input,
            current_iteration=current_iteration + 1,
            max_iterations=max_iterations,
            current_strategy=cognitive_state.get("current_strategy", "initial_approach"),
            previous_attempts=attempts_summary,
            last_tool_quality=cognitive_state.get("last_tool_quality", "unknown")
        )
    except Exception:
        # Fallback to simple reasoning if enhanced prompt fails
        reasoning_prompt = f"""Analyze the conversation and decide your next action.
        
        ORIGINAL QUERY: {context.current_input}
        AVAILABLE TOOLS: {tool_info}
        
        Output JSON format: {{"reasoning": "your reasoning", "strategy": "approach_name"}}
        """
    
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"
    
    messages.insert(0, {"role": "system", "content": reasoning_prompt})
    
    try:
        llm_response = await llm.run(messages)
        context.add_message("assistant", llm_response)
        
        # Parse response using consolidated utilities
        json_data = extract_json_from_response(llm_response)
        tool_calls = extract_tool_calls_from_json(json_data)
        
        # Extract strategy from JSON if provided (graceful fallback)
        try:
            current_strategy = json_data.get("strategy", "unknown") if json_data else "unknown"
        except Exception:
            current_strategy = "fallback_strategy"
        
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
    
    # Assess previous tool execution results if available
    execution_results = state.get("execution_results")
    if execution_results:
        tool_quality = assess_tool_quality(execution_results)
        cognitive_state["last_tool_quality"] = tool_quality
        
        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                track_failed_attempt(cognitive_state, prev_tool_calls, tool_quality, current_iteration)
    
    # Update cognitive state for next iteration
    if tool_calls:
        action_fingerprint = create_action_fingerprint(tool_calls)
        update_cognitive_state(cognitive_state, tool_calls, current_strategy, action_fingerprint)
    
    # Store current tool calls for next iteration's assessment
    state["prev_tool_calls"] = tool_calls
    
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


