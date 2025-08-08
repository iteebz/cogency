"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.events import emit
from cogency.state import State


async def execute_agent(state: State, triage_step, reason_step, act_step, synthesize_step) -> None:
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
        # Always call synthesize after response
        await synthesize_step(state)
        emit(
            "agent_complete",
            source="triage",
            iterations=state.execution.iteration,
            response=state.execution.response,
        )
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
            # Always call synthesize after response
            await synthesize_step(state)
            emit(
                "agent_complete",
                source="reason",
                iterations=state.execution.iteration,
                response=state.execution.response,
            )
            return
        elif response and not isinstance(response, Result):
            emit("reason", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "reason"
            # Always call synthesize after response
            await synthesize_step(state)
            emit(
                "agent_complete",
                source="reason",
                iterations=state.execution.iteration,
                response=state.execution.response,
            )
            return

        emit(
            "reason",
            state="complete",
            early_return=False,
            tool_calls=len(state.execution.pending_calls),
        )

        # No tool calls means completion - either with response or graceful exit
        if not state.execution.pending_calls:
            break

        # Act step
        response = await act_step(state)
        if isinstance(response, Result):
            if response.success and response.data:
                state.execution.response = response.data
                state.execution.response_source = "act"
                # Always call synthesize after response
                await synthesize_step(state)
                emit(
                    "agent_complete",
                    source="act",
                    iterations=state.execution.iteration,
                    response=state.execution.response,
                )
                return
            # On failure, loop continues, error is in tool_results
        elif response:
            emit("action", state="complete", early_return=True)
            state.execution.response = response
            state.execution.response_source = "act"
            # Always call synthesize after response
            await synthesize_step(state)
            emit(
                "agent_complete",
                source="act",
                iterations=state.execution.iteration,
                response=state.execution.response,
            )
            return

        if state.execution.stop_reason:
            emit("react_exit", reason=state.execution.stop_reason)
            break

    # Natural completion - use response if available
    if not state.execution.response:
        state.execution.response = "Task completed."
        state.execution.response_source = "natural"
    await synthesize_step(state)
    emit("agent_complete", source="natural", iterations=state.execution.iteration)
