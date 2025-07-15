#!/usr/bin/env python3
"""
Basic usage example for Cogency - demonstrates calculator and web search tools

Run with: cd ../python && poetry run python ../examples/basic_usage.py
"""

import os
import sys

from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools.calculator import CalculatorTool
from cogency.tools.web_search import WebSearchTool


async def main():
    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY=your-api-key")
        sys.exit(1)

    # Create LLM instance (new cleaner interface)
    llm = GeminiLLM(api_keys=api_key)

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