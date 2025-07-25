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
    parse_switch,
    should_switch,
    summarize_attempts,
    switch_mode,
)
from cogency.nodes.reasoning.deep import (
    prompt_deep_mode,
)
from cogency.nodes.reasoning.fast import (
    prompt_fast_mode,
)
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.registry import build_registry
from cogency.types.errors import ParsingError, format_parsing_error, format_reasoning_error
from cogency.types.reasoning import Reasoning
from cogency.utils.parsing import parse_json_with_correction

logger = logging.getLogger(__name__)


def build_iterations(cognition, selected_tools, max_iterations=3):
    """Show last N reasoning iterations with their outcomes."""
    iteration_entries = cognition.iterations
    failed_attempts = summarize_attempts(cognition.failed_attempts)

    if not iteration_entries:
        return (
            failed_attempts
            if failed_attempts != "No previous failed attempts"
            else "No previous iterations"
        )

    iterations = []
    last_iterations = iteration_entries[-max_iterations:]

    for entry in last_iterations:
        if not entry or not isinstance(entry, dict):
            continue

        iteration_num = entry.get("iteration", 0)
        fingerprint = entry.get("fingerprint", "unknown")
        result = entry.get("result", "")

        if result:
            iterations.append(f"Iteration {iteration_num}: {fingerprint}\n→ {result}")
        else:
            iterations.append(f"Iteration {iteration_num}: {fingerprint}")

    iteration_summary = "\n".join(iterations)

    # Include failures if they exist
    if failed_attempts != "No previous failed attempts":
        return f"PREVIOUS ITERATIONS:\n{iteration_summary}\n\nFAILED ATTEMPTS:\n{failed_attempts}"

    return f"PREVIOUS ITERATIONS:\n{iteration_summary}"


def format_actions(execution_results, prev_tool_calls, selected_tools):
    """Extract formatted results from previous execution for agent context."""
    if not (execution_results and hasattr(execution_results, "data") and execution_results.data):
        return ""

    results_data = execution_results.data
    if not (isinstance(results_data, dict) and "results" in results_data):
        return ""

    formatted_parts = []
    results_list = results_data["results"]

    for _i, (tool_call, result_entry) in enumerate(zip(prev_tool_calls, results_list)):
        tool_name = tool_call.get("name", "unknown")

        # Find the tool and call its format_agent method
        for tool in selected_tools:
            if tool.name == tool_name:
                if hasattr(tool, "format_agent"):
                    # The result is now in result_entry["result"] not result_entry.data
                    result_data = result_entry.get("result", {})
                    agent_format = tool.format_agent(result_data)
                    formatted_parts.append(agent_format)
                break

    return " | ".join(formatted_parts) if formatted_parts else ""


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
    selected_tools = state.selected_tools or tools or []

    # Simple iteration tracking
    iter = state.current_iteration
    max_iter = state.max_iterations

    # Initialize cognitive state - start fast, let LLM discover complexity
    react_mode = state.react_mode

    # Set react mode if different from current
    if state.cognition.react_mode != react_mode:
        state.cognition.react_mode = react_mode

    # Start reasoning state with simplified messaging
    await state.output.state("reasoning", react_mode)

    # Adaptive loop detection based on mode
    if react_mode == "deep":
        try:
            loop_detected = detect_loop(state.cognition)
        except Exception as e:
            logger.error(f"Deep loop detection failed: {e}")
            loop_detected = False  # Fallback to no loop detection if it fails
    else:
        # Fast react: lightweight loop detection with lower threshold
        try:
            loop_detected = detect_fast_loop(state.cognition)
        except Exception as e:
            logger.error(f"Fast loop detection failed: {e}")
            loop_detected = False  # Fallback gracefully

    if iter >= max_iter:
        # Stop reasoning after max iterations with user-friendly message
        user_message = format_reasoning_error("max_iterations")
        await state.output.trace(user_message, node="reason")
        state["stopping_reason"] = "max_iterations_reached"
        state["user_error_message"] = user_message
        state["tool_calls"] = None
        return state
    elif loop_detected:
        # Stop reasoning if loop detected with user-friendly message
        user_message = format_reasoning_error("loop_detected")
        await state.output.trace(user_message, node="reason")
        state["stopping_reason"] = "reasoning_loop_detected"
        state["user_error_message"] = user_message
        state["tool_calls"] = None
        return state

    tool_registry = build_registry(selected_tools)

    messages = list(context.messages)
    messages.append({"role": "user", "content": context.query})

    # Create unified iteration history for both modes
    attempts_summary = build_iterations(state.cognition, selected_tools, max_iterations=3)

    # Hide verbose iteration history - only show for debugging if needed
    # await state.output.trace(f"Iteration history: {attempts_summary}", node="reason")

    # Build adaptive reasoning prompt - with reflection for deep mode
    if react_mode == "deep":
        # Deep mode: use explicit reflection phases
        current_approach = state.cognition.current_approach
        last_tool_quality = state.cognition.last_tool_quality
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
        # Fast mode: use streamlined fast reasoning with preserved context
        preserved_context = getattr(state.cognition, "preserved_context", "")
        reasoning_prompt = prompt_fast_mode(
            tool_registry, context.query, attempts_summary, preserved_context
        )

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

        # Create trace function for parsing feedback
        def trace_parsing(msg: str):
            asyncio.create_task(state.output.trace(msg, node="reason"))

        # Parse response with self-correction and tracing
        parse_result = await parse_json_with_correction(
            llm_response, llm_fn=llm.run, trace_fn=trace_parsing, max_attempts=2
        )

        if not parse_result.success:
            # Create ParsingError for detailed tracking
            parsing_error = ParsingError(
                parse_result.error,
                raw_response=llm_response[:200] + "..."
                if len(llm_response) > 200
                else llm_response,
                correction_attempts=2,  # We attempted 2 corrections
            )

            # Log technical details for debugging
            await state.output.trace(
                f"JSON parsing failed after all attempts: {parse_result.error}", node="reason"
            )

            # Show user-friendly parsing-specific message
            user_message = format_parsing_error("self_correction_failed")
            await state.output.trace(user_message, node="reason")

            # Track parsing failure separately from reasoning failure
            state["parsing_error"] = parsing_error
            state["last_error_type"] = "parsing"

            # Fallback to empty Reasoning object if parsing fails
            json_data = Reasoning()
        else:
            json_data = parse_result.data
            # Clear any previous parsing errors on success
            state["parsing_error"] = None
            state["last_error_type"] = None
            # Explicitly create Reasoning object from parsed data
            json_data = Reasoning.from_dict(json_data)

        # Show reasoning phases - gated by verbose flag
        verbose = state.get("verbose", True)  # Default to True for backward compatibility
        if verbose:
            if react_mode == "deep" and json_data:
                thinking_phase = json_data.thinking
                reflect_phase = json_data.reflect
                plan_phase = json_data.plan

                if thinking_phase:
                    await state.output.update(f"💭 {thinking_phase}\n")
                if reflect_phase:
                    await state.output.update(f"🤔 {reflect_phase}\n")
                if plan_phase:
                    await state.output.update(f"📋 {plan_phase}\n")
            elif json_data and json_data.thinking:
                thinking = json_data.thinking
                if thinking:
                    await state.output.update(f"💭 {thinking}\n")

        # Initialize variables that need to be available throughout the function
        tool_calls = None

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

        # Parse tool calls from JSON - reasoning should never provide direct responses
        tool_calls = json_data.tool_calls

        state["tool_calls"] = tool_calls

        # Show thinking instantly (not streamed)
        reasoning = json_data.reasoning
        if reasoning:
            pass  # Reasoning is now a list of strings, handled by output.update in flow.py

        state["reasoning_response"] = llm_response
        # No direct responses from reasoning - only JSON with tool calls or empty

        # Hide internal reasoning - users don't need to see this ceremony
        current_approach = "unified_react"

    except Exception as e:
        logger.error(f"Reasoning process failed: {e}")
        # Handle LLM or parsing errors gracefully with user-friendly message
        user_message = format_reasoning_error("unknown_error")
        await state.output.trace(user_message, node="reason")

        # Default to responding directly when reasoning fails
        tool_calls = None
        state["stopping_reason"] = "reasoning_error"
        state["user_error_message"] = user_message
        state["tool_calls"] = tool_calls
        # Reasoning node never provides direct responses - respond node handles ALL responses
        state["direct_response"] = None
        state["can_answer_directly"] = True
        state["reasoning_response"] = user_message

        # Hide error reasoning - users don't need to see ceremony
        current_approach = "unified_react"

    # Assess previous tool execution results if available
    execution_results = state.execution_results
    if execution_results:
        tool_quality = assess_tools(execution_results)
        state.cognition.set_tool_quality(tool_quality)

        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                state.cognition.track_failure(prev_tool_calls, tool_quality, iter)

    # Update cognitive state for next iteration
    if tool_calls:
        fingerprint = action_fingerprint(tool_calls)
        # Extract decision from reasoning data
        if react_mode == "deep":
            current_decision = json_data.reasoning[0] if json_data.reasoning else "unknown"
        else:
            current_decision = json_data.reasoning[0] if json_data.reasoning else "unknown"

        # Store current iteration without formatted results (will be added after execution)
        state.cognition.update(
            tool_calls, current_approach, current_decision, fingerprint, "", iter + 1
        )

    # Store current tool calls for next iteration's assessment
    state["prev_tool_calls"] = tool_calls

    # Increment iteration counter
    state["current_iteration"] = iter + 1

    # Store tool calls for routing (flow.py handles the routing logic)
    state["tool_calls"] = tool_calls

    return state
