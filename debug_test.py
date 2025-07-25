#!/usr/bin/env python3
"""Debug test to see what's happening with respond function."""

import asyncio
from cogency.context import Context
from cogency.nodes.respond import respond
from cogency.output import Output
from .conftest import MockLLM
from cogency.state import State


async def debug_respond():
    # Setup test state
    ctx = Context("test query")
    ctx.add_message("user", "What is the weather?")
    state = State(context=ctx, query="test query", output=Output())

    # Create mock LLM
    llm = MockLLM(response="Hello world")

    print("Initial state keys:", list(state.flow.keys()))
    print("State before call:", state)
    print("State id before:", id(state))

    try:
        # Call respond
        updated_state = await respond(state, llm=llm, tools=[])

        print("Final state type:", type(updated_state))
        print("State id after:", id(updated_state))
        print("Same object?", updated_state is state)

        # Check original state
        print("Original state now has final_response?", "final_response" in state.flow)
        if "final_response" in state.flow:
            print("Original state final_response:", state["final_response"])

        if hasattr(updated_state, "flow"):
            print("Final state keys:", list(updated_state.flow.keys()))
            print("final_response present:", "final_response" in updated_state.flow)
            if "final_response" in updated_state.flow:
                print("final_response value:", updated_state["final_response"])
            else:
                print("Available keys:", list(updated_state.flow.keys()))
        else:
            print(
                "State is dict with keys:",
                list(updated_state.keys()) if isinstance(updated_state, dict) else "Not a dict",
            )
            if isinstance(updated_state, dict) and "final_response" in updated_state:
                print("final_response value:", updated_state["final_response"])

    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_respond())
