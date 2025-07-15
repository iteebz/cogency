#!/usr/bin/env python3
"""Multi-step reasoning with state management - the full power."""
import asyncio
from cogency import Agent, CalculatorTool, WebSearchTool

async def main():
    # Complex agent with memory and tools
    agent = Agent(
        "research_analyst",
        tools=[CalculatorTool(), WebSearchTool()],
        temperature=0.3  # More focused
    )

    # Multi-step reasoning task
    task = """
    1. Find the current price of Bitcoin
    2. Calculate how much 0.5 Bitcoin would cost
    3. Research the latest Bitcoin news
    4. Provide investment recommendation
    """

    result = await agent.run(task)

    print("🧠 FULL ANALYSIS:")
    print(result)

    # Agent maintains state across calls
    followup = await agent.run("What if I bought $1000 worth instead?")
    print("\n💡 FOLLOWUP ANALYSIS:")
    print(followup)

if __name__ == "__main__":
    asyncio.run(main())