#!/usr/bin/env python3
"""Multi-tool workflow: Research + code generation pattern."""

import asyncio

from cogency import Agent
from cogency.tools import Code, Search


async def main():
    print("🔍➡️🚀 RESEARCH + CODE WORKFLOW")
    print("=" * 40 + "\n")

    # Agent with search and code execution
    agent = Agent(
        "research_coder",
        identity="research assistant who finds information then implements solutions",
        tools=[Search(), Code()],
        memory=False,
        depth=8,
        trace=True,
        # deep=True,  # Force deep mode
        # adapt=False,  # Disable adaptive switching
    )

    # Query that requires research then implementation
    query = """I need to implement a simple algorithm to check if a number is prime.

    First, research what makes an efficient prime checking algorithm, 
    then implement and test it with a few examples like 17, 25, and 97."""

    print("🎯 WORKFLOW QUERY:")
    print(f"{query}\n")
    print("=" * 40)

    try:
        result = await agent.run(query)
        print(f"\n✅ WORKFLOW RESULT:\n{result}")
    except Exception as e:
        print(f"\n❌ WORKFLOW ERROR: {e}")

    print("\n" + "=" * 40)
    print("🎵 Expected workflow:")
    print("  1. Search for prime number algorithm information")
    print("  2. Analyze search results for best approach")
    print("  3. Implement prime checking algorithm in code")
    print("  4. Test with provided examples")
    print("  5. Present research findings + working code")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
