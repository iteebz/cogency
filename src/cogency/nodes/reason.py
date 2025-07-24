"""Reason node - pure reasoning and decision making."""

import asyncio
import logging
from typing import List, Optional

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
    prompt_deep_mode,
)
from cogency.nodes.reasoning.fast import (
    prompt_fast_mode,
)
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.utils.parsing import parse_json_result, parse_tool_calls, recover_json
from cogency.tools.registry import build_registry

logger = logging.getLogger(__name__)


def build_iteration_history(cognition, selected_tools, max_iterations=3):
    """Show last N reasoning iterations with their outcomes."""
    fingerprints = cognition.get("action_fingerprints", [])
    failed_attempts = summarize_attempts(cognition.get("failed_attempts", []))
    
    if not fingerprints:
        return failed_attempts if failed_attempts != "No previous failed attempts" else "No previous iterations"
    
    iterations = []
    for i, fp in enumerate(fingerprints[-max_iterations:]):
        step_num = len(fingerprints) - max_iterations + i + 1
        iterations.append(f"Step {step_num}: {fp}")
    
    iteration_summary = "\n".join(iterations)
    
    # Include failures if they exist
    if failed_attempts != "No previous failed attempts":
        return f"PREVIOUS ITERATIONS:\n{iteration_summary}\n\nFAILED ATTEMPTS:\n{failed_attempts}"
    
    return f"PREVIOUS ITERATIONS:\n{iteration_summary}"



async def reason(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None,
    identity: Optional[str] = None,
) -> State:
    """Analyze context and decide next action with adaptive reasoning."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])

    # Simple iteration tracking
    iter = state.get("current_iteration", 0)
    max_iter = state.get("max_iterations", 5)

    # Initialize cognitive state - start fast, let LLM discover complexity
    react_mode = state.get("react_mode", "fast")

    cognition = init_cognition(state, react_mode=react_mode)

    # Start reasoning state with simplified messaging
    await state.output.state("reasoning", react_mode)

    # Adaptive loop detection based on mode
    if react_mode == "deep":
        try:
            loop_detected = detect_loop(cognition)
        except Exception as e:
            logger.error(f"Deep loop detection failed: {e}")
            loop_detected = False  # Fallback to no loop detection if it fails
    else:
        # Fast react: lightweight loop detection with lower threshold
        try:
            loop_detected = detect_fast_loop(cognition)
        except Exception as e:
            logger.error(f"Fast loop detection failed: {e}")
            loop_detected = False  # Fallback gracefully

    if iter >= max_iter:
        # Stop reasoning after max iterations
        state["stopping_reason"] = "max_iterations_reached"
        state["tool_calls"] = None
        return state
    elif loop_detected:
        # Stop reasoning if loop detected
        state["stopping_reason"] = "reasoning_loop_detected"
        state["tool_calls"] = None
        return state

    tool_registry = build_registry(selected_tools)

    messages = list(context.messages)
    messages.append({"role": "user", "content": context.query})

    # Create unified iteration history for both modes
    attempts_summary = build_iteration_history(cognition, selected_tools, max_iterations=3)

    # Build adaptive reasoning prompt - with reflection for deep mode
    if react_mode == "deep":
        # Deep mode: use explicit reflection phases
        current_approach = cognition.get("current_approach", "initial")
        last_tool_quality = cognition.get("last_tool_quality", "unknown")
        reasoning_prompt = prompt_deep_mode(
            tool_registry,
            context.query,
            iter,
            max_iter,
            current_approach,
            attempts_summary,
            last_tool_quality,
        )
    else:
        # Fast mode: use streamlined fast reasoning 
        reasoning_prompt = prompt_fast_mode(tool_registry, context.query, attempts_summary)

    # Simple identity flow - just add it
    if identity:
        reasoning_prompt = f"{identity}\n\n{reasoning_prompt}"

    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"

    messages.insert(0, {"role": "system", "content": reasoning_prompt})

    try:
        # Yield control to allow state message to appear immediately
        await asyncio.sleep(0)
        llm_response = await llm.run(messages)

        # Don't add reasoning JSON to context - it's internal planning only

        # Parse response using consolidated utilities
        parse_result = parse_json_result(llm_response)
        if not parse_result.success:
            await state.output.trace(f"JSON parsing failed: {parse_result.error}", node="reason")
            # Fallback to empty dict if parsing fails
            json_data = {}
        else:
            json_data = parse_result.data

        # Show reasoning phases - gated by verbose flag
        verbose = state.get("verbose", True)  # Default to True for backward compatibility
        if verbose:
            if react_mode == "deep" and json_data:
                assess_phase = json_data.get("assess", "")
                reflect_phase = json_data.get("reflect", "")
                plan_phase = json_data.get("plan", "")
                decide_phase = json_data.get("decide", "")

                if assess_phase:
                    await state.output.update(f"⚖️ {assess_phase}\n")
                if reflect_phase:
                    await state.output.update(f"🤔 {reflect_phase}\n")
                if plan_phase:
                    await state.output.update(f"📋 {plan_phase}\n")
                if decide_phase:
                    await state.output.update(f"🎯 {decide_phase}\n")
            elif json_data and json_data.get("thinking"):
                thinking = json_data.get("thinking")
                if thinking:
                    await state.output.update(f"\n💭 {thinking}\n")

        # Initialize variables that need to be available throughout the function
        tool_calls = None
        can_answer = True

        # Reasoning should always output JSON - if not, try to recover
        if not isinstance(json_data, dict) or not json_data:
            json_data = recover_json(llm_response)

            if not json_data:
                state["stopping_reason"] = "invalid_json_format"
                state["tool_calls"] = None
                return state
        else:
            # Check for bidirectional mode switching
            switch_to, switch_why = parse_switch(llm_response)
            if should_switch(react_mode, switch_to, switch_why, iter):
                await state.output.trace(
                    f"Mode switch: {react_mode} → {switch_to} ({switch_why})",
                    node="reason",
                )
                state = switch_mode(state, switch_to, switch_why)
                # Update react_mode for this iteration
                react_mode = switch_to

            # Handle direct response from recovered JSON
            if "response" in json_data and json_data.get("tool_calls") is None:
                # This is a direct response that was recovered from non-JSON
                state["direct_response"] = json_data["response"]
                state["can_answer_directly"] = True
                state["tool_calls"] = None
                tool_calls = None
                can_answer = True
            else:
                tool_calls = parse_tool_calls(json_data)
                can_answer = tool_calls is None or len(tool_calls) == 0

                state["can_answer_directly"] = can_answer
                state["tool_calls"] = tool_calls

            # Show thinking instantly (not streamed)
            reasoning = json_data.get("reasoning", "Processing...")
            if isinstance(reasoning, dict):
                # Deep mode - show decision
                if reasoning.get("decision"):
                    pass  # No longer used
                else:
                    pass  # No longer used
            else:
                pass  # No longer used

            state["reasoning_response"] = llm_response
            # No direct responses from reasoning - only JSON with tool calls or empty

        # Hide internal reasoning - users don't need to see this ceremony
        current_approach = "unified_react"

    except Exception as e:
        logger.error(f"Reasoning process failed: {e}")
        # Handle LLM or parsing errors gracefully - store in state, not conversation
        # Default to responding directly when reasoning fails
        can_answer = True
        tool_calls = None
        llm_response = "I encountered an issue with reasoning, but I'll do my best to help you."

        # Store reasoning results in state - NO JSON LEAKAGE
        state["reasoning_response"] = llm_response
        state["can_answer_directly"] = can_answer
        state["tool_calls"] = tool_calls
        # Reasoning node never provides direct responses - respond node handles ALL responses
        state["direct_response"] = None

        # Hide error reasoning - users don't need to see ceremony
        current_approach = "unified_react"

    # Assess previous tool execution results if available
    execution_results = state.get("execution_results")
    if execution_results:
        tool_quality = assess_tools(execution_results)
        cognition["last_tool_quality"] = tool_quality

        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                track_failure(cognition, prev_tool_calls, tool_quality, iter)

    # Update cognitive state for next iteration
    if tool_calls:
        fingerprint = action_fingerprint(tool_calls)
        # Extract decision from reasoning data
        if react_mode == "deep":
            reasoning_obj = json_data.get("reasoning", {})
            current_decision = (
                reasoning_obj.get("decision", "unknown")
                if isinstance(reasoning_obj, dict)
                else "unknown"
            )
        else:
            current_decision = json_data.get("reasoning", "unknown")
        update_cognition(cognition, tool_calls, current_approach, current_decision, fingerprint)

    # Store current tool calls for next iteration's assessment
    state["prev_tool_calls"] = tool_calls

    # Increment iteration counter
    state["current_iteration"] = iter + 1

    # Store tool calls for routing (flow.py handles the routing logic)
    state["tool_calls"] = tool_calls

    return state
