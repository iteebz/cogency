#!/usr/bin/env python3
"""Debug script to see exactly what prompt goes to reasoning system."""

import asyncio

from cogency.agent import Agent


async def debug_reasoning_prompt():
    print("=== DEBUGGING REASONING PROMPT ===")

    # Create agent with memory
    agent = Agent("assistant", memory=True)

    # Store some memory
    await agent.run("My name is PromptDebugger and I work on AI systems", user_id="debug_user")

    # Patch the LLM to capture the actual prompt
    original_generate = agent.llm.generate
    captured_prompt = None

    async def capture_prompt(*args, **kwargs):
        nonlocal captured_prompt
        if args:
            captured_prompt = args[0]  # First argument should be messages
        return await original_generate(*args, **kwargs)

    agent.llm.generate = capture_prompt

    # Run a query that should use memory
    response, conversation_id = await agent.run(
        "What is my name and what do I do?", user_id="debug_user"
    )
    print("\n=== AGENT RESPONSE ===")
    print(response)

    # Show the captured prompt
    if captured_prompt:
        print("\n" + "=" * 80)
        print("FULL REASONING PROMPT FOR HUMAN VALIDATION")
        print("=" * 80)
        for i, msg in enumerate(captured_prompt):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            print(f"\n{'='*20} Message {i+1}: {role.upper()} {'='*20}")
            print(content)
            print("=" * 80)
    else:
        print("No prompt captured!")


if __name__ == "__main__":
    asyncio.run(debug_reasoning_prompt())
