"""Reason node - pure reasoning and decision making."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.state import AgentState

from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, extract_reasoning_text
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
from cogency.nodes.reasoning.loop_detection import detect_fast_mode_loop
from cogency.nodes.reasoning.adaptation import (
    extract_mode_switch,
    should_switch_modes,
    execute_mode_switch
)
from cogency.nodes.reasoning.reflection import (
    get_deep_reflection_prompt,
    extract_reflection_phases,
    format_reflection_for_display,
    should_use_reflection
)
from cogency.nodes.reasoning.planning import (
    extract_planning_strategy,
    validate_planning_quality,
    create_multi_step_plan,
    format_plan_for_display
)
from cogency.nodes.reasoning.prompts import build_reasoning_prompt




async def reason_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], system_prompt: Optional[str] = None, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Reason: analyze context and decide next action (includes implicit reflection)."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    
    # Simple iteration tracking
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    
    # Initialize cognitive state with adaptive features based on react_mode
    react_mode = state.get("react_mode", "fast")
    cognitive_state = initialize_cognitive_state(state, react_mode=react_mode)
    
    # Adaptive loop detection based on mode
    if react_mode == "deep":
        try:
            loop_detected = detect_action_loop(cognitive_state)
        except Exception:
            loop_detected = False  # Fallback to no loop detection if it fails
    else:
        # Fast react: lightweight loop detection with lower threshold
        try:
            loop_detected = detect_fast_mode_loop(cognitive_state)
        except Exception:
            loop_detected = False  # Fallback gracefully
    
    if current_iteration >= max_iterations:
        # Stop reasoning after max iterations
        state["stopping_reason"] = "max_iterations_reached"
        state["next_node"] = "respond"
        return state
    elif loop_detected:
        # Stop reasoning if loop detected
        await state.output.send("trace", "Loop detected - stopping reasoning", node="reason")
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
    
    # Build adaptive reasoning prompt
    reasoning_prompt = build_reasoning_prompt(
        react_mode,
        current_iteration,
        tool_info,
        context.current_input,
        max_iterations,
        cognitive_state,
        attempts_summary
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
        
        # Extract strategy from JSON if provided (graceful fallback)
        try:
            current_strategy = json_data.get("strategy", "unknown") if json_data else "unknown"
        except Exception:
            current_strategy = "fallback_strategy"
        
        # Check for bidirectional mode switching
        switch_to, switch_reason = extract_mode_switch(llm_response)
        if should_switch_modes(react_mode, switch_to, switch_reason, current_iteration):
            await state.output.send("trace", f"Mode switch: {react_mode} → {switch_to} ({switch_reason})", node="reason")
            state = execute_mode_switch(state, switch_to, switch_reason)
            # Update react_mode for this iteration
            react_mode = switch_to
        
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
    await state.output.send("update", reasoning_text)
    
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
        
        # Trace tool quality assessment
        await state.output.send("trace", f"Tool performance assessment: {tool_quality}", node="reason")
        
        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                failed_tools = [call.get("function", {}).get("name", "unknown") for call in prev_tool_calls]
                await state.output.send("trace", f"Tracking failed attempt: {', '.join(failed_tools)}", node="reason")
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




