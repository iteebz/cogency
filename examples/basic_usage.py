#!/usr/bin/env python3
"""
Basic usage example for Cogency - demonstrates calculator and web search tools

Run with: cd ../python && poetry run python ../examples/basic_usage.py
"""

from cogency.agent import Agent
from cogency.llm import auto_detect_llm
from cogency.tools.calculator import CalculatorTool
from cogency.tools.web_search import WebSearchTool


async def main():
    # Auto-detect LLM from environment - MAGICAL!
    llm = auto_detect_llm()

    # Create agent with tools
    agent = Agent(
        name="DemoAgent",
        llm=llm,
        tools=[CalculatorTool(), WebSearchTool()]
    )

    # Example 1: Calculator
    print("=== Calculator Example ===")
    result = await agent.run("What is 127 * 43?")
    print(f"Response: {result}")
    print()

    # Example 2: Web Search
    print("=== Web Search Example ===")
    result = await agent.run("What are the latest developments in AI?")
    print(f"Response: {result}")
    print()

    # Example 3: Combined reasoning
    print("=== Combined Reasoning Example ===")
    result = await agent.run(
        "Search for the current stock price of NVIDIA and calculate what 100 shares would cost"
    )
    print(f"Response: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())