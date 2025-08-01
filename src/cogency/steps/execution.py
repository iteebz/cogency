"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.state import State


async def run_agent(
    state: State, prepare_phase, reason_phase, act_phase, respond_phase, notifier=None
) -> None:
    """Pure early-return execution - phases decide when to end."""

    # Prepare - may return early
    response = await prepare_phase(state, notifier)
    if response:
        state.response = response
        state.response_source = "prepare"
        # Always call respond for identity application
        await respond_phase(state, notifier)
        return

    # ReAct loop - reason and act until early return
    while state.iteration < state.depth:
        # Reason phase
        response = await reason_phase(state, notifier)
        if response:
            state.response = response
            state.response_source = "reason"
            # Always call respond for identity application
            await respond_phase(state, notifier)
            return

        # If no tool calls, exit ReAct loop
        if not state.tool_calls:
            break

        # Act phase
        response = await act_phase(state, notifier)
        if response:
            state.response = response
            state.response_source = "act"
            return

        state.iteration += 1

        if state.stop_reason:
            break

    # Respond phase - fallback
    await respond_phase(state, notifier)
    if not state.response:
        state.response = "I'm here to help. How can I assist you?"
