#!/usr/bin/env python3
"""Test recursion fix without LangGraph."""

import asyncio

from src.cogency.agent import Agent
from src.cogency.tools.base import BaseTool


class TestTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="test_tool", description="A test tool that always returns 'test result'"
        )

    async def run(self, query: str) -> str:
        return f"Test result for: {query}"


async def main():
    # Create agent with max 3 iterations to test recursion limit
    tools = [TestTool()]
    agent = Agent("test", tools=tools, max_iterations=3, trace=True, verbose=True)

    # This should NOT hit recursion limit - agent should stop after getting results
    result = await agent.run("Use test_tool to help me")
    print(f"Result: {result}")
    print(f"Final state: {agent.last_state}")


if __name__ == "__main__":
    asyncio.run(main())
