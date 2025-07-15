#!/usr/bin/env python3
"""PARALLEL EXECUTION - Test multiple tools working together."""
import asyncio
from cogency import Agent, CalculatorTool, WeatherTool, TimezoneTool

async def main():
    # Agent with multiple tools for parallel execution testing
    agent = Agent(
        "multi_tool_analyst", 
        tools=[CalculatorTool(), WeatherTool(), TimezoneTool()]
    )

    print("🎯 TESTING PARALLEL EXECUTION")
    print("=" * 50)

    # Task that should trigger parallel execution
    task = """
    I need multiple pieces of information:
    1. Calculate 15 * 24 
    2. Get weather for London
    3. What time is it in Tokyo timezone?
    """

    print(f"🤖 Query: \"{task}\"")
    print()
    
    result = await agent.run(task)

    print("\n🧠 PARALLEL EXECUTION RESULT:")
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ Advanced parallel execution test complete!")

if __name__ == "__main__":
    asyncio.run(main())