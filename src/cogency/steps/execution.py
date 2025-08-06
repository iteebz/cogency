"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.events import emit
from cogency.state import AgentState


async def execute_agent(
    state: AgentState, triage_step, reason_step, act_step, respond_step, synthesize_step
) -> None:
    """Early-return execution."""
    emit(
        "agent_start",
        level="debug",
        mode=state.execution.mode,
        max_iterations=state.execution.max_iterations,
    )

    # Triage - may return early
    emit("triage", level="debug", state="start")
    if response := await triage_step(state):
        emit("triage", state="complete", early_return=True)
        state.execution.response = response
        state.execution.response_source = "triage"
        # Always call respond for identity application
        emit("respond", level="debug", state="start", source="triage")
        await respond_step(state)
        # Always call synthesize after response
        await synthesize_step(state)
        emit("agent_complete", source="triage", iterations=state.execution.iteration)
        return

    # ReAct loop - reason and act until early return
    emit("triage", state="complete", early_return=False)
    max_iter = state.execution.max_iterations or 50  # Default to 50 if None
    while state.execution.iteration < max_iter:
        state.execution.iteration += 1
        emit("react_iteration", level="debug", iteration=state.execution.iteration)

        # Reason step
        emit("reason", level="debug", state="start", iteration=state.execution.iteration)
        response = await reason_step(state)
        from resilient_result import Result

        if isinstance(response, Result) and response.success and response.data:
            emit("reason", state="complete", early_return=True)
            state.execution.response = response.data
            state.execution.response_source = "reason"
            # Always call respond for identity application
            emit("respond", level="debug", state="start", source="reason")
            await respond_step(state)
            # Always call synthesize after response
            await synthesize_step(state)
            emit("agent_complete", source="reason", iterations=state.execution.iteration)
            return
        elif response and not isinstance(response, Result):
            emit("reason", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "reason"
            emit("respond", level="debug", state="start", source="reason")
            await respond_step(state)
            # Always call synthesize after response
            await synthesize_step(state)
            emit("agent_complete", source="reason", iterations=state.execution.iteration)
            return

        emit(
            "reason",
            state="complete",
            early_return=False,
            tool_calls=len(state.execution.pending_calls),
        )

        # If no tool calls, trust the LLM's decision to complete
        if not state.execution.pending_calls:
            emit("react_exit", level="debug", reason="no_tool_calls")
            break

        # Act step
        response = await act_step(state)
        if isinstance(response, Result):
            if response.success and response.data:
                state.execution.response = response.data
                state.execution.response_source = "act"
                # Always call synthesize after response
                await synthesize_step(state)
                emit("agent_complete", source="act", iterations=state.execution.iteration)
                return
            # On failure, loop continues, error is in tool_results
        elif response:
            emit("action", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "act"
            # Always call synthesize after response
            await synthesize_step(state)
            emit("agent_complete", source="act", iterations=state.execution.iteration)
            return

        if state.execution.stop_reason:
            emit("react_exit", reason=state.execution.stop_reason)
            break

    # No fallback - if we reach here, something went wrong
    emit("agent_error", reason="execution_incomplete", iterations=state.execution.iteration)
    state.execution.response = f"Agent failed to complete task after {state.execution.iteration} iterations. The LLM may not be generating valid responses."
    state.execution.response_source = "error"
    await synthesize_step(state)
