"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.state import State


async def execute_agent(
    state: State, prepare_step, reason_step, act_step, respond_step, notifier=None
) -> None:
    """Pure early-return execution - phases decide when to end."""
    # Prepare - may return early
    response = await prepare_step(state, notifier)
    if response:
        state.response = response
        state.response_source = "prepare"
        # Always call respond for identity application
        await respond_step(state, notifier)
        return

    # ReAct loop - reason and act until early return
    while state.iteration < state.depth:
        # Reason phase
        response = await reason_step(state, notifier)
        from resilient_result import Result

        if isinstance(response, Result) and response.success and response.data:
            state.response = response.data
            state.response_source = "reason"
            # Always call respond for identity application
            await respond_step(state, notifier)
            return
        elif response and not isinstance(response, Result):
            state.response = response
            state.response_source = "reason"
            await respond_step(state, notifier)
            return

        # If no tool calls, exit ReAct loop
        if not state.tool_calls:
            break

        # Act phase
        response = await act_step(state, notifier)
        if isinstance(response, Result) and response.success and response.data:
            state.response = response.data
            state.response_source = "act"
            return
        elif response and not isinstance(response, Result):
            state.response = response
            state.response_source = "act"
            return

        state.iteration += 1

        if state.stop_reason:
            break

    # Respond phase - fallback
    await respond_step(state, notifier)
    if not state.response:
        state.response = "I'm here to help. How can I assist you?"
