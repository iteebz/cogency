"""Reason node - pure reasoning and decision making."""

import asyncio
from typing import List, Optional

from cogency.decorators import phase
from cogency.phases.base import Phase
from cogency.phases.reasoning import parse_switch, prompt_reasoning, should_switch, switch_mode
from cogency.services import LLM
from cogency.state import State
from cogency.tools import Tool, build_registry
from cogency.types.reasoning import Reasoning
from cogency.utils.parsing import parse_json_with_correction


class Reason(Phase):
    def __init__(self, llm, tools, identity=None):
        super().__init__(reason, llm=llm, tools=tools, identity=identity)

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
            key_args = {
                k: v for k, v in args.items() if k in ["query", "url", "filename", "command"]
            }
            if key_args:
                args_str = ", ".join(f"{k}={v}" for k, v in key_args.items())
                parts.append(f"{name}({args_str})")
            else:
                parts.append(name)
        else:
            parts.append(name)

    return " | ".join(parts)


def build_iterations(state, selected_tools, depth=3):
    """Build reasoning context using State methods (schema-compliant)."""
    context_parts = []

    # Latest results (fresh output from most recent action)
    latest_results = state.get_latest_results()
    if latest_results:
        for call in latest_results:
            result_snippet = call.get("result", "")[:200] + (
                "..." if len(call.get("result", "")) > 200 else ""
            )
            context_parts.append(f"Latest: {call['name']}() → {result_snippet}")

    # Compressed history (past actions)
    from cogency.state import compress_actions

    compressed = compress_actions(state.actions[-depth:] if depth else state.actions)
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


@phase.reason()
async def reason(
    state: State,
    notifier,
    llm: LLM,
    tools: List[Tool],
    identity: Optional[str] = None,
) -> None:
    """Pure reasoning orchestration - let decorators handle all ceremony."""
    # Direct access to state properties - no context wrapper needed
    selected_tools = state.selected_tools or tools or []
    mode = state.mode
    iteration = state.iteration

    # Set react mode if different from current
    if state.mode != mode:
        state.mode = mode

    await notifier("reason", state=mode)

    # Check stop conditions - pure logic, no ceremony
    if iteration >= state.depth:
        state.stop_reason = "depth_reached"
        state.tool_calls = None
        await notifier(
            "trace", message="ReAct terminated", reason="depth_reached", iterations=iteration
        )
        return  # State mutated in place

    # Build messages
    messages = state.get_conversation()
    messages.append({"role": "user", "content": state.query})

    # Build unified prompt with mode-specific context
    tool_registry = build_registry(selected_tools)

    # Phase 2B/3: Use clean context assembly
    context = state.build_reasoning_context(mode, max_history=3)

    reasoning_prompt = prompt_reasoning(
        mode=mode,
        tool_registry=tool_registry,
        query=state.query,
        context=context,
        iteration=iteration,
        depth=state.depth,
        state=state,
    )

    # Trace reasoning context for debugging
    if iteration == 0:
        await notifier("trace", message="ReAct loop initiated", mode=mode, depth_limit=state.depth)

    # Add optional identity prompt
    if identity:
        reasoning_prompt = f"{identity}\n\n{reasoning_prompt}"

    messages.insert(0, {"role": "system", "content": reasoning_prompt})

    # LLM reasoning - let decorator handle errors
    await asyncio.sleep(0)  # Yield for UI
    llm_result = await llm.run(messages)
    from resilient_result import unwrap

    raw_response = unwrap(llm_result)

    # Parse with correction
    parse_result = await parse_json_with_correction(raw_response, llm_fn=llm.run, max_attempts=2)

    reasoning_response = (
        Reasoning.from_dict(parse_result.data) if parse_result.success else Reasoning()
    )

    # Trace parsing failures for debugging
    if not parse_result.success:
        await notifier(
            "trace",
            message="LLM response parse failed",
            mode=mode,
            iteration=iteration,
            error="invalid_reasoning_format",
        )

    # Display reasoning phases
    if mode == "deep" and reasoning_response:
        if reasoning_response.thinking:
            await notifier("reason", state="thinking", content=reasoning_response.thinking)
        if reasoning_response.reflect:
            await notifier("reason", state="reflect", content=reasoning_response.reflect)
        if reasoning_response.plan:
            await notifier("reason", state="plan", content=reasoning_response.plan)
    elif reasoning_response.thinking:
        await notifier("reason", state="thinking", content=reasoning_response.thinking)

    # Handle mode switching - only if agent mode is "adapt"
    agent_mode = getattr(state, "agent_mode", "adapt")
    if agent_mode == "adapt":
        switch_to, switch_why = parse_switch(raw_response)
        if should_switch(mode, switch_to, switch_why, iteration, state.depth):
            await notifier(
                "trace",
                message="Mode switch executed",
                from_mode=mode,
                to_mode=switch_to,
                reason=switch_why,
                iteration=iteration,
            )
            state = switch_mode(state, switch_to, switch_why)

    # Update reasoning state
    tool_calls = reasoning_response.tool_calls
    update_reasoning_state(state, tool_calls, reasoning_response, iteration)

    # Update state for next iteration
    state.tool_calls = tool_calls
    state.iteration = state.iteration + 1

    # State mutated in place, no return needed


def update_reasoning_state(state, tool_calls, reasoning_response, iteration: int) -> None:
    """Update reasoning state after iteration."""
    # Add action to reasoning history (tool results added later in act node)
    if tool_calls:
        # Get the current action to update with compression fields
        state.add_action(
            mode=state.mode,
            thinking=reasoning_response.thinking or "",
            planning=getattr(reasoning_response, "plan", "") or "",
            reflection=getattr(reasoning_response, "reflect", "") or "",
            approach=state.approach,
            tool_calls=tool_calls,
        )

        # Update cognitive workspace
        if reasoning_response.workspace_update:
            state.update_workspace(reasoning_response.workspace_update)
