#!/usr/bin/env python3
"""See the agent think in real-time - transparent reasoning."""
import asyncio
from cogency import Agent, CalculatorTool, WebSearchTool

async def main():
    agent = Agent("analyst", tools=[CalculatorTool(), WebSearchTool()])

    print("🤔 Analyzing NVIDIA stock...")
    async for chunk in agent.stream("Find NVIDIA's current stock price and calculate the value of 100 shares"):
        if chunk["type"] == "thinking":
            print(f"💭 {chunk['content']}")
        elif chunk["type"] == "tool_call":  
            print(f"🔧 Using: {chunk['content']}")
        elif chunk["type"] == "result":
            print(f"✅ Found: {chunk['data']}")

    print("\n🎯 Stream = Execution. No black boxes.")

if __name__ == "__main__":
    asyncio.run(main())