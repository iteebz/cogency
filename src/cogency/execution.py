"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.state import State


async def run_agent(state: State, preprocess_phase, reason_phase, act_phase, respond_phase) -> None:
    """Simple execution loop using phase instances with injected dependencies."""

    # Preprocessing step - dependencies already injected
    await preprocess_phase(state)

    # Main reasoning loop
    while state.iteration < state.max_iterations:
        # Reason about what to do
        await reason_phase(state)

        # If no tools needed, break to response
        if not state.tool_calls:
            break

        # Execute tools
        await act_phase(state)

        # Increment iteration
        state.iteration += 1

        # Check stop conditions
        if state.stop_reason:
            break

    # Generate final response
    await respond_phase(state)
