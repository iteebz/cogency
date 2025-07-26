"""Reason node - pure reasoning and decision making."""

import asyncio
from typing import List, Optional

from cogency.nodes.reasoning.adaptive import (
    action_fingerprint,
    assess_tools,
    parse_switch,
    should_stop_reasoning,
    should_switch,
    summarize_attempts,
    switch_mode,
)
from cogency.nodes.reasoning.deep import prompt_deep_mode
from cogency.nodes.reasoning.fast import prompt_fast_mode
from cogency.resilience import safe
from cogency.services.llm import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.registry import build_registry
from cogency.types.reasoning import Reasoning
from cogency.utils.parsing import parse_json_with_correction


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


@safe.checkpoint("reason")
@safe.reason()
async def reason(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None,
    identity: Optional[str] = None,
) -> State:
    """Pure reasoning orchestration - let decorators handle all ceremony."""
    context = state["context"]
    selected_tools = state.selected_tools or tools or []
    react_mode = state.react_mode
    iteration = state.iteration

    # Set react mode if different from current
    if state.cognition.react_mode != react_mode:
        state.cognition.react_mode = react_mode

    await state.output.state("reasoning", react_mode)

    # Check stop conditions - pure logic, no ceremony
    should_stop, stop_reason = should_stop_reasoning(state, react_mode)
    if should_stop:
        state["stop_reason"] = stop_reason
        state["tool_calls"] = None
        return state

    # Build messages
    messages = list(context.chat)
    messages.append({"role": "user", "content": context.query})

    # Build prompt based on mode
    attempts_summary = build_iterations(state.cognition, selected_tools, max_iterations=3)
    tool_registry = build_registry(selected_tools)

    if react_mode == "deep":
        reasoning_prompt = prompt_deep_mode(
            tool_registry,
            context.query,
            iteration,
            state.max_iterations,
            state.cognition.current_approach,
            attempts_summary,
            state.cognition.last_tool_quality,
        )
    else:
        preserved_context = getattr(state.cognition, "preserved_context", "")
        reasoning_prompt = prompt_fast_mode(
            tool_registry, context.query, attempts_summary, preserved_context
        )

    # Add optional prompts
    if identity:
        reasoning_prompt = f"{identity}\n\n{reasoning_prompt}"
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"

    messages.insert(0, {"role": "system", "content": reasoning_prompt})

    # LLM reasoning - let decorator handle errors
    await asyncio.sleep(0)  # Yield for UI
    llm_result = await llm.run(messages)
    from cogency.resilience import unwrap

    raw_response = unwrap(llm_result)

    # Parse with correction
    def trace_parsing(msg: str):
        asyncio.create_task(state.output.trace(msg, node="reason"))

    parse_result = await parse_json_with_correction(
        raw_response, llm_fn=llm.run, trace_fn=trace_parsing, max_attempts=2
    )

    reasoning_response = (
        Reasoning.from_dict(parse_result.data) if parse_result.success else Reasoning()
    )

    # Display reasoning phases
    if state.get("verbose", True):
        if react_mode == "deep" and reasoning_response:
            if reasoning_response.thinking:
                await state.output.update(f"💭 {reasoning_response.thinking}\n")
            if reasoning_response.reflect:
                await state.output.update(f"🤔 {reasoning_response.reflect}\n")
            if reasoning_response.plan:
                await state.output.update(f"📋 {reasoning_response.plan}\n")
        elif reasoning_response.thinking:
            await state.output.update(f"💭 {reasoning_response.thinking}\n")

    # Handle mode switching
    switch_to, switch_why = parse_switch(raw_response)
    if should_switch(react_mode, switch_to, switch_why, iteration):
        await state.output.trace(
            f"Mode switch: {react_mode} → {switch_to} ({switch_why})", node="reason"
        )
        state = switch_mode(state, switch_to, switch_why)

    # Update cognitive state
    tool_calls = reasoning_response.tool_calls
    update_cognitive_state(state, tool_calls, reasoning_response, iteration)

    # Update state for next iteration
    state["reasoning"] = raw_response
    state["tool_calls"] = tool_calls
    state["prev_tool_calls"] = tool_calls
    state["iteration"] = state["iteration"] + 1

    return state


def update_cognitive_state(state, tool_calls, reasoning_response, iteration: int) -> None:
    """Update cognitive state after reasoning iteration."""
    # Assess previous tool execution results
    result = state.result
    if result:
        tool_quality = assess_tools(result)
        state.cognition.set_tool_quality(tool_quality)

        # Track failed attempts for loop prevention
        if tool_quality in ["failed", "poor"]:
            prev_tool_calls = state.get("prev_tool_calls", [])
            if prev_tool_calls:
                state.cognition.track_failure(prev_tool_calls, tool_quality, iteration)

    # Update cognitive state for next iteration
    if tool_calls:
        fingerprint = action_fingerprint(tool_calls)
        current_decision = (
            reasoning_response.reasoning[0] if reasoning_response.reasoning else "unknown"
        )

        state.cognition.update(
            tool_calls, "unified_react", current_decision, fingerprint, "", iteration + 1
        )
