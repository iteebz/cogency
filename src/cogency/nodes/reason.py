"""Reason node - pure reasoning and decision making."""

from typing import Any, Dict, List, Optional

from cogency.llm import BaseLLM
from cogency.nodes.reasoning.adaptive import (
    action_fingerprint,
    assess_tools,
    detect_fast_loop,
    detect_loop,
    init_cognition,
    parse_switch,
    should_switch,
    summarize_attempts,
    switch_mode,
    track_failure,
    update_cognition,
)
from cogency.nodes.reasoning.deep import (
    format_deep_mode,
    parse_deep_mode,
    prompt_deep_mode,
)
from cogency.nodes.reasoning.fast import (
    parse_fast_mode,
    prompt_fast_mode,
)
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.utils import parse_json
from cogency.utils.parsing import parse_tool_calls


async def reason(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None,
    config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Analyze context and decide next action with adaptive reasoning."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])

    # Simple iteration tracking
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    # Initialize cognitive state with adaptive features based on react_mode
    react_mode = state.get("react_mode", "fast")
    cognition = init_cognition(state, react_mode=react_mode)

    # Adaptive loop detection based on mode
    if react_mode == "deep":
        try:
            loop_detected = detect_loop(cognition)
        except Exception:
            loop_detected = False  # Fallback to no loop detection if it fails
    else:
        # Fast react: lightweight loop detection with lower threshold
        try:
            loop_detected = detect_fast_loop(cognition)
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
            schema = t.schema()
            examples = getattr(t, "examples", lambda: [])()
            if examples:
                example_str = " Examples: " + ", ".join(examples[:2])  # Show first 2 examples
                tool_info_parts.append(f"{t.name}: {schema}.{example_str}")
            else:
                tool_info_parts.append(f"{t.name}: {schema}")
        tool_info = "\n".join(tool_info_parts)
    else:
        tool_info = "no tools"

    messages = list(context.messages)
    messages.append({"role": "user", "content": context.query})

    # Create attempts summary from failed attempts
    failed_attempts = cognition.get("failed_attempts", [])
    attempts_summary = summarize_attempts(failed_attempts)

    # Build adaptive reasoning prompt - with reflection for deep mode
    if react_mode == "deep":
        # Deep mode: use explicit reflection phases
        current_approach = cognition.get("current_approach", "initial")
        last_tool_quality = cognition.get("last_tool_quality", "unknown")
        reasoning_prompt = prompt_deep_mode(
            tool_info,
            context.query,
            current_iteration,
            max_iterations,
            current_approach,
            attempts_summary,
            last_tool_quality,
        )
    else:
        # Fast mode: use streamlined fast reasoning
        reasoning_prompt = prompt_fast_mode(tool_info, context.query)

    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"

    messages.insert(0, {"role": "system", "content": reasoning_prompt})

    try:
        llm_response = await llm.run(messages)
        context.add_message("assistant", llm_response)

        # Parse response using consolidated utilities
        json_data = parse_json(llm_response)
        tool_calls = parse_tool_calls(json_data)

        # Check for bidirectional mode switching
        switch_to, switch_reason = parse_switch(llm_response)
        if should_switch(react_mode, switch_to, switch_reason, current_iteration):
            await state.output.send(
                "trace", f"Mode switch: {react_mode} → {switch_to} ({switch_reason})", node="reason"
            )
            state = switch_mode(state, switch_to, switch_reason)
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

    # Extract and stream reasoning - with reflection phases for deep mode
    if react_mode == "deep":
        # Deep mode: extract and display reflection phases
        thinking_phase = parse_deep_mode(llm_response)
        deep_thinking = format_deep_mode(thinking_phase)
        await state.output.send("update", deep_thinking)

        # Store deep thought data for tracing
        cognition["last_deep_thought"] = thinking_phase
        await state.output.send(
            "trace",
            f"Deep thinking: approach={thinking_phase.get('decision', 'unknown')}",
            node="reason",
        )

        # Extract approach from deep thinking phase
        current_approach = thinking_phase.get("decision", "unknown")
    else:
        # Fast mode: standard reasoning extraction
        reasoning_data = parse_fast_mode(llm_response)
        reasoning_text = f"💭 {reasoning_data.get('thinking', 'Processing...')} | ⚡ {reasoning_data.get('decision', 'Acting...')}"
        await state.output.send("update", reasoning_text)

        # Extract approach from fast mode
        current_approach = reasoning_data.get("decision", "unknown")

    # Store reasoning results in state - NO JSON LEAKAGE
    state["reasoning_response"] = llm_response
    state["can_answer_directly"] = can_answer
    state["tool_calls"] = tool_calls
    # Reasoning node never provides direct responses - respond node handles ALL responses
    state["direct_response"] = None

    # Assess previous tool execution results if available
    execution_results = state.get("execution_results")
    if execution_results:
        tool_quality = assess_tools(execution_results)
        cognition["last_tool_quality"] = tool_quality

        # Trace tool quality assessment
        await state.output.send(
            "trace", f"Tool performance assessment: {tool_quality}", node="reason"
        )

        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                failed_tools = [
                    call.get("function", {}).get("name", "unknown") for call in prev_tool_calls
                ]
                await state.output.send(
                    "trace", f"Tracking failed attempt: {', '.join(failed_tools)}", node="reason"
                )
                track_failure(cognition, prev_tool_calls, tool_quality, current_iteration)

    # Update cognitive state for next iteration
    if tool_calls:
        fingerprint = action_fingerprint(tool_calls)
        # Extract decision from reasoning data
        if react_mode == "deep":
            current_decision = thinking_phase.get("decision", "unknown")
        else:
            current_decision = reasoning_data.get("decision", "unknown")
        update_cognition(cognition, tool_calls, current_approach, current_decision, fingerprint)

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
