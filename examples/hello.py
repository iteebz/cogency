#!/usr/bin/env python3
"""Hello World - Character Demo with Sherlock Holmes"""

import asyncio

from cogency import Agent
from cogency.utils import demo_header, trace_args, section, stream_response


async def main():
    demo_header("🔥 Cogency Character Demo")

    user = "👤 HUMAN: "
    sherlock = "🕵️ SHERLOCK: "

    # Sherlock Holmes character
    agent = Agent(
        "Sherlock",
        identity="""Sherlock Holmes, the famous detective.
        Speak in his distinctive Victorian style with deductive reasoning.
        Keep responses concise and brilliant.
        Always respond with plain text only, no markdown formatting""",
        tools=[],
        memory=False,
        trace=trace_args(),
    )

    # Mystery deduction
    query_1 = "I found a muddy footprint by my window this morning. What happened?"
    print(f"\n{user}{query_1}\n")
    await stream_response(agent.stream(query_1), prefix=sherlock)

    # Quick observation
    query_2 = "Someone left coffee rings on my desk. Who was here?"
    print(f"\n\n{user}{query_2}\n")
    await stream_response(agent.stream(query_2), prefix=sherlock)

    # Interactive detective session
    print("\n")
    section("Detective Session with Holmes (type 'quit' to exit)")
    print("🔍 Present your mysteries to the great detective...")

    while True:
        try:
            user_input = input(f"\n\n{user}").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Good day!")
                break
            if user_input:
                print()
                await stream_response(agent.stream(user_input), prefix=sherlock)
        except KeyboardInterrupt:
            print("\n👋 Good day!")
            break


if __name__ == "__main__":
    asyncio.run(main())
