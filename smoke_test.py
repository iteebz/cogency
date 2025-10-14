import asyncio

from cogency import Agent


async def main():
    """
    Smoke test for Cogency's resume mode with OpenAI Realtime API.
    """
    print("--- Starting Cogency Smoke Test ---")

    # Use a unique conversation ID for the test
    test_conversation_id = f"smoke-test-{asyncio.get_event_loop().time()}"

    agent = Agent(llm="openai", mode="resume")

    print("--- Test Run 1: Initial Question ---")
    print(f"Conversation ID: {test_conversation_id}")
    print("User: What is the capital of France?")

    response_1 = []
    async for event in agent(
        "What is the capital of France?",
        conversation_id=test_conversation_id,
        user_id="smoke-tester",
    ):
        if event["type"] == "respond":
            response_1.append(event["content"])
            print(f"Agent (raw): {event['content']}")
            print(f"Agent: {event['content']}")

    full_response_1 = "".join(response_1)
    if "paris" not in full_response_1.lower():
        print("!!! TEST FAILED: Did not receive expected response for first question.")
        return

    print("\n--- Test Run 2: Follow-up Question ---")
    print("User: What about Germany?")

    response_2 = []
    # Continue the *same* conversation
    async for event in agent(
        "What about Germany?", conversation_id=test_conversation_id, user_id="smoke-tester"
    ):
        if event["type"] == "respond":
            response_2.append(event["content"])
            print(f"Agent: {event['content']}")

    full_response_2 = "".join(response_2)
    if "berlin" not in full_response_2.lower():
        print("!!! TEST FAILED: Did not receive expected response for follow-up question.")
        return

    print("\n--- Smoke Test Passed! ---")


if __name__ == "__main__":
    # This is a temporary script, so we handle the poetry environment manually.
    # In a real scenario, this would be run via `poetry run python smoke_test.py`
    import os
    import sys

    # Assuming the script is run from the `public/cogency` directory
    # and the .venv is in that directory.
    venv_path = os.path.join(os.getcwd(), ".venv/bin/python")
    if not os.path.exists(venv_path):
        print(
            "Could not find the virtual environment. Please run from the `public/cogency` directory."
        )
        sys.exit(1)

    # This is a hack to run the async main function.
    # A better approach would be to use `poetry run`
    os.system(f"{venv_path} -c 'import asyncio; from smoke_test import main; asyncio.run(main())'")
