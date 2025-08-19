#!/usr/bin/env python3
"""Simple one-off Cogency agent invocation script."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cogency import Agent
from cogency.tools import BASIC_TOOLS


async def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/ask.py 'your question here' [--no-tools] [--llm=provider] [--max-iterations=N]"
        )
        print("Examples:")
        print("  python scripts/ask.py 'What is 2+2?'")
        print("  python scripts/ask.py 'Create a Python script to add numbers' --max-iterations=10")
        print("  python scripts/ask.py 'Explain async/await' --no-tools")
        print("  python scripts/ask.py 'Complex task' --llm=anthropic")
        return

    # Parse arguments
    question = sys.argv[1]
    use_tools = True
    llm_provider = "openai"
    max_iterations = 5

    debug = False

    for arg in sys.argv[2:]:
        if arg == "--no-tools":
            use_tools = False
        elif arg == "--debug":
            debug = True
        elif arg.startswith("--llm="):
            llm_provider = arg.split("=")[1]
        elif arg.startswith("--max-iterations="):
            max_iterations = int(arg.split("=")[1])

    # Create agent
    tools = BASIC_TOOLS if use_tools else None
    agent = Agent(llm=llm_provider, tools=tools, max_iterations=max_iterations)

    # Show reasoning mode
    print(
        f"🤖 Cogency Agent ({llm_provider}, {'with' if use_tools else 'no'} tools, max_iterations={max_iterations})"
    )
    print(f"❓ Question: {question}")
    print("─" * 50)

    # Generate canonical identifiers
    user_id = "ask_user"
    conversation_id = f"ask_{int(__import__('time').time())}"

    if debug:
        # Show the actual prompt that will be sent to LLM
        from cogency.context.assembly import context

        print("🔍 DEBUG MODE: Assembled Context")
        print("=" * 60)

        # Convert tools list to dict format
        tools_dict = {tool.name: tool for tool in tools} if tools else {}

        prompt = context.assemble(question, user_id, conversation_id, user_id, tools_dict)
        print(prompt)

        print("=" * 60)
        print()

    # Clear conversation history for clean testing
    from cogency.context.conversation import conversation

    conversation.clear(conversation_id)

    try:
        response = await agent(question, user_id=user_id, conversation_id=conversation_id)
        print(response)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
