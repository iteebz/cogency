#!/usr/bin/env python3
"""Persistent Memory - Core Architectural Differentiator"""

import asyncio

from cogency import Agent
from cogency.utils import demo_header, trace_args, stream_response


async def main():
    demo_header("🧠 Cogency Memory Demo")

    user = "👤 HUMAN: "
    assistant = "🤖 ASSISTANT: "

    # Create agent with memory enabled and only recall tool
    from cogency.tools import Recall

    agent = Agent(
        "memory_assistant",
        identity="helpful assistant with excellent memory",
        memory_dir=".cogency/demo_memory",  # Custom memory location for demo
        tools=[Recall],  # Only recall tool - memory is the star
        trace=trace_args(),
    )

    # Teaching the Agent
    query_1 = """Please remember these important details about me:
    - My name is Alex and I'm a software engineer
    - I work primarily with Python and JavaScript
    - My favorite framework is FastAPI for backends
    - I'm currently building a personal finance app
    - I prefer concise, practical advice over long explanations
    """
    print(f"\n{user}{query_1}\n")
    await stream_response(agent.stream(query_1), prefix=assistant)

    # Testing Memory Recall
    query_2 = "What do you know about my work and preferences?"
    print(f"\n\n{user}{query_2}\n")
    await stream_response(agent.stream(query_2), prefix=assistant)

    # Context + Memory Working Together
    query_3 = "Based on what you know about me, what would be a good database choice for my current project?"
    print(f"\n\n{user}{query_3}\n")
    await stream_response(agent.stream(query_3), prefix=assistant)


if __name__ == "__main__":
    asyncio.run(main())
