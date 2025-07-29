"""Simple execution loop - zero ceremony, zero kwargs."""

from cogency.state import State


async def run_agent(
    state: State, preprocess_phase, reason_phase, act_phase, respond_phase, notifier=None
) -> None:
    """Simple execution loop using phase instances with injected dependencies."""

    # Preprocessing step - dependencies already injected
    await preprocess_phase(state, notifier)

    # Two execution paths: direct response OR ReAct loop
    if not state.respond_directly:
        # ReAct loop: reason until ready to respond
        while state.iteration < state.depth:
            # Reason about what to do
            await reason_phase(state, notifier)

            # If ready to respond, break to response
            if not state.tool_calls:
                break

            # Act on the tools (execute them)
            await act_phase(state, notifier)

            # Increment iteration after complete ReAct cycle
            state.iteration += 1

            # Check stop conditions
            if state.stop_reason:
                break

    # Generate final response (both paths converge here)
    await respond_phase(state, notifier)
