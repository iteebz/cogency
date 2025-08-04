"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.events import emit
from cogency.state import AgentState


async def execute_agent(
    state: AgentState, triage_step, reason_step, act_step, respond_step, synthesize_step
) -> None:
    """Early-return execution."""
    emit("agent_start", mode=state.execution.mode, max_iterations=state.execution.max_iterations)

    # Triage - may return early
    emit("triage", state="start")
    if response := await triage_step(state):
        emit("triage", state="complete", early_return=True)
        state.execution.response = response
        state.execution.response_source = "triage"
        # Always call respond for identity application
        emit("respond", state="start", source="triage")
        await respond_step(state)
        # Always call synthesize after response
        await synthesize_step(state)
        emit("agent_complete", source="triage", iterations=state.execution.iteration)
        return

    # ReAct loop - reason and act until early return
    emit("triage", state="complete", early_return=False)
    while state.execution.iteration < state.execution.max_iterations:
        state.execution.iteration += 1
        emit("react_iteration", iteration=state.execution.iteration)

        # Reason step
        emit("reason", state="start", iteration=state.execution.iteration)
        response = await reason_step(state)
        from resilient_result import Result

        if isinstance(response, Result) and response.success and response.data:
            emit("reason", state="complete", early_return=True)
            state.execution.response = response.data
            state.execution.response_source = "reason"
            # Always call respond for identity application
            emit("respond", state="start", source="reason")
            await respond_step(state)
            # Always call synthesize after response
            await synthesize_step(state)
            emit("agent_complete", source="reason", iterations=state.execution.iteration)
            return
        elif response and not isinstance(response, Result):
            emit("reason", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "reason"
            emit("respond", state="start", source="reason")
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

        # If no tool calls, exit ReAct loop
        if not state.execution.pending_calls:
            emit("react_exit", reason="no_tool_calls")
            break

        # Act step
        emit("action", state="start", tool_count=len(state.execution.pending_calls))
        response = await act_step(state)
        if isinstance(response, Result):
            if response.success and response.data:
                emit("action", state="complete", early_return=True)
                state.execution.response = response.data
                state.execution.response_source = "act"
                # Always call synthesize after response
                await synthesize_step(state)
                emit("agent_complete", source="act", iterations=state.execution.iteration)
                return
            # On failure, loop continues, error is in tool_results
            emit("action", state="complete", early_return=False, success=False)
        elif response:
            emit("action", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "act"
            # Always call synthesize after response
            await synthesize_step(state)
            emit("agent_complete", source="act", iterations=state.execution.iteration)
            return
        else:
            emit("action", state="complete", early_return=False)

        if state.execution.stop_reason:
            emit("react_exit", reason=state.execution.stop_reason)
            break

    # Respond step - fallback
    emit("respond", state="start", source="fallback")
    await respond_step(state)
    if not state.execution.response:
        state.execution.response = "I'm here to help. How can I assist you?"
    # Always call synthesize after response
    await synthesize_step(state)
    emit("agent_complete", source="fallback", iterations=state.execution.iteration)
