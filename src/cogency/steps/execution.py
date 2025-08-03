"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.state import AgentState


async def execute_agent(
    state: AgentState, prepare_step, reason_step, act_step, respond_step, notifier=None
) -> None:
    """Early-return execution."""
    # Prepare - may return early
    if response := await prepare_step(state, notifier):
        state.execution.response = response
        state.execution.response_source = "prepare"
        # Always call respond for identity application
        await respond_step(state, notifier)
        return

    # ReAct loop - reason and act until early return
    while state.execution.iteration < state.execution.max_iterations:
        # Reason phase
        response = await reason_step(state, notifier)
        from resilient_result import Result

        if isinstance(response, Result) and response.success and response.data:
            state.execution.response = response.data
            state.execution.response_source = "reason"
            # Always call respond for identity application
            await respond_step(state, notifier)
            return
        elif response and not isinstance(response, Result):
            state.execution.response = response
            state.execution.response_source = "reason"
            await respond_step(state, notifier)
            return

        # If no tool calls, exit ReAct loop
        if not state.execution.pending_calls:
            break

        # Act phase
        response = await act_step(state, notifier)
        if isinstance(response, Result):
            if response.success and response.data:
                state.execution.response = response.data
                state.execution.response_source = "act"
                return
            # On failure, loop continues, error is in tool_results
        elif response:
            state.execution.response = response
            state.execution.response_source = "act"
            return

        state.execution.iteration += 1

        if state.execution.stop_reason:
            break

    # Respond phase - fallback
    await respond_step(state, notifier)
    if not state.execution.response:
        state.execution.response = "I'm here to help. How can I assist you?"
