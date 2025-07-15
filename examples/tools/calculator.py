#!/usr/bin/env python3
"""Calculator tool isolation test."""
import asyncio
from cogency import Agent, CalculatorTool

async def main():
    print("🧮 Testing CalculatorTool...")
    agent = Agent("calc", tools=[CalculatorTool()])
    result = await agent.run("Calculate 15 * 23")
    assert "345" in str(result), f"Expected 345, got: {result}"

if __name__ == "__main__":
    asyncio.run(main())