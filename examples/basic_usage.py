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


def main():
    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY=your-api-key")
        sys.exit(1)

    # Create LLM instance
    llm = GeminiLLM(api_key=api_key)

    # Create agent with tools
    agent = Agent(
        name="DemoAgent",
        llm=llm,
        tools=[CalculatorTool(), WebSearchTool()]
    )

    # Example 1: Calculator
    print("=== Calculator Example ===")
    result = agent.run("What is 127 * 43?", enable_trace=True, print_trace=True)
    print(f"Response: {result['response']}")
    print()

    # Example 2: Web Search
    print("=== Web Search Example ===")
    result = agent.run("What are the latest developments in AI?", enable_trace=True, print_trace=True)
    print(f"Response: {result['response']}")
    print()

    # Example 3: Combined reasoning
    print("=== Combined Reasoning Example ===")
    result = agent.run(
        "Search for the current stock price of NVIDIA and calculate what 100 shares would cost",
        enable_trace=True,
        print_trace=True
    )
    print(f"Response: {result['response']}")


if __name__ == "__main__":
    main()