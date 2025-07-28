"""Reason node - pure reasoning and decision making."""

import asyncio
from typing import List, Optional

from cogency.phases.base import Node
from cogency.constants import ADAPT_REACT
from cogency.phases.reasoning import (
    parse_switch,
    should_switch,
    switch_mode,
)
from cogency.phases.reasoning.deep import prompt_deep_mode
from cogency.phases.reasoning.fast import prompt_fast_mode
from cogency.resilience import robust
from cogency.services.llm import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.registry import build_registry
from cogency.types.reasoning import Reasoning
from cogency.utils.parsing import parse_json_with_correction


class Reason(Node):
    def __init__(self, **kwargs):
        super().__init__(reason, **kwargs)

    def next_phase(self, state: State) -> str:
        return "act" if state.tool_calls and len(state.tool_calls) > 0 else "respond"


def format_tool_calls_readable(tool_calls):
    """Format tool calls as readable action summary."""
    if not tool_calls:
        return "no_action"
    
    parts = []
    for call in tool_calls:
        name = call.get("name", "unknown")
        args = call.get("args", {})
        
        if isinstance(args, dict) and args:
            key_args = {k: v for k, v in args.items() if k in ["query", "url", "filename", "command"]}
            if key_args:
                args_str = ", ".join(f"{k}={v}" for k, v in key_args.items())
                parts.append(f"{name}({args_str})")
            else:
                parts.append(name)
        else:
            parts.append(name)
    
    return " | ".join(parts)


def build_iterations(state, selected_tools, max_iterations=3):
    """Build reasoning context using State methods (schema-compliant)."""
    context_parts = []
    
    # Latest results (fresh output from most recent action)
    latest_results = state.get_latest_results()
    if latest_results:
        for call in latest_results:
            result_snippet = call.get("result", "")[:200] + ("..." if len(call.get("result", "")) > 200 else "")
            context_parts.append(f"Latest: {call['name']}() → {result_snippet}")
    
    # Compressed history (past actions)
    compressed = state.get_compressed_attempts(max_history=max_iterations)
    if compressed:
        context_parts.extend([f"Prior: {attempt}" for attempt in compressed])
    
    return "; ".join(context_parts) if context_parts else "No previous attempts"


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


# @robust.reason()  # DISABLED FOR DEBUGGING
async def reason(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None,
    identity: Optional[str] = None,
) -> State:
    """Pure reasoning orchestration - let decorators handle all ceremony."""
    # Direct access to state properties - no context wrapper needed
    selected_tools = state.selected_tools or tools or []
    react_mode = state.react_mode
    iteration = state.iteration

    # Set react mode if different from current
    if state.react_mode != react_mode:
        state.react_mode = react_mode

    await state.notify("state_change", {"state": "reasoning", "mode": react_mode})

    # Check stop conditions - pure logic, no ceremony
    if iteration >= state.max_iterations:
        state.stop_reason = "max_iterations_reached"
        state.tool_calls = None
        return state

    # Build messages
    messages = state.get_conversation()
    messages.append({"role": "user", "content": state.query})

    # Build prompt based on mode with mode-specific limits
    tool_registry = build_registry(selected_tools)

    if react_mode == "deep":
        attempts_summary = build_iterations(state, selected_tools, max_iterations=10)
        reasoning_prompt = prompt_deep_mode(
            tool_registry,
            state.query,
            iteration,
            state.max_iterations,
            state.current_approach,
            attempts_summary,
            "unknown",  # TODO: derive from latest action outcome
        )
    else:
        attempts_summary = build_iterations(state, selected_tools, max_iterations=3)
        reasoning_prompt = prompt_fast_mode(tool_registry, state.query, attempts_summary)
    
    # DEBUG: Show what LLM sees
    if state.trace:
        await state.notify("trace", {"message": f"Iteration {iteration}: attempts_summary = '{attempts_summary}'", "phase": "reason"})

    # Add optional prompts
    if identity:
        reasoning_prompt = f"{identity}\n\n{reasoning_prompt}"
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"

    messages.insert(0, {"role": "system", "content": reasoning_prompt})

    # LLM reasoning - let decorator handle errors
    await asyncio.sleep(0)  # Yield for UI
    llm_result = await llm.run(messages)
    from resilient_result import unwrap

    raw_response = unwrap(llm_result)

    # Parse with correction
    def trace_parsing(msg: str):
        if state.trace:
            asyncio.create_task(state.notify("trace", {"message": msg, "phase": "reason"}))

    parse_result = await parse_json_with_correction(
        raw_response, llm_fn=llm.run, trace_fn=trace_parsing, max_attempts=2
    )

    reasoning_response = (
        Reasoning.from_dict(parse_result.data) if parse_result.success else Reasoning()
    )

    # Display reasoning phases
    if state.verbose:
        if react_mode == "deep" and reasoning_response:
            if reasoning_response.thinking:
                await state.notify("update", f"💭 {reasoning_response.thinking}\n")
            if reasoning_response.reflect:
                await state.notify("update", f"🤔 {reasoning_response.reflect}\n")
            if reasoning_response.plan:
                await state.notify("update", f"📋 {reasoning_response.plan}\n")
        elif reasoning_response.thinking:
            await state.notify("update", f"💭 {reasoning_response.thinking}\n")

    # Handle mode switching (disabled for debugging)
    if ADAPT_REACT:
        switch_to, switch_why = parse_switch(raw_response)
        if should_switch(react_mode, switch_to, switch_why, iteration):
            if state.trace:
                await state.notify(
                    "trace", f"Mode switch: {react_mode} → {switch_to} ({switch_why})", node="reason"
                )
            state = switch_mode(state, switch_to, switch_why)
    elif state.trace:
        await state.notify("trace", {"message": "Mode switching disabled (ADAPT_REACT=False)", "phase": "reason"})

    # Update reasoning state
    tool_calls = reasoning_response.tool_calls
    update_reasoning_state(state, tool_calls, reasoning_response, iteration)

    # Update state for next iteration
    state.tool_calls = tool_calls
    state.iteration = state.iteration + 1

    return state


def update_reasoning_state(state, tool_calls, reasoning_response, iteration: int) -> None:
    """Update reasoning state after iteration."""
    # Add action to reasoning history (tool results added later in act node)
    if tool_calls:
        state.add_action(
            mode=state.react_mode,
            thinking=reasoning_response.thinking or "",
            planning=getattr(reasoning_response, 'plan', "") or "",
            reflection=getattr(reasoning_response, 'reflect', "") or "",
            approach=state.current_approach,
            tool_calls=tool_calls,
        )
