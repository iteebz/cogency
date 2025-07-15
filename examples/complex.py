#!/usr/bin/env python3
"""ADVANCED CHAINING - Multi-step problem solving with tool dependencies."""
import asyncio
from cogency import Agent
from cogency import CalculatorTool, WeatherTool, TimezoneTool

async def main():
    # Agent with multiple tools for complex problem solving
    agent = Agent(
        "travel_planner", 
        tools=[CalculatorTool(), WeatherTool(), TimezoneTool()]
    )

    print("🎯 ADVANCED MULTI-STEP PROBLEM SOLVING")
    print("=" * 50)

    # Complex scenario requiring tool chaining and dependencies
    scenario = """
    I'm planning a business trip to London and need to prepare:
    
    1. First, what's the current weather in London so I know what to pack?
    2. What time is it there right now? (I need to schedule calls)
    3. If my flight costs $1,200 and hotel is $180 per night for 3 nights, 
       what's my total accommodation cost?
    4. What's the total trip cost (flight + hotel)?
    
    Please work through this step-by-step.
    """

    print(f"🤖 Scenario: {scenario}")
    print()
    
    result = await agent.run(scenario, mode="trace")

    print("\n🧠 MULTI-STEP SOLUTION:")
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ Advanced chaining demo complete!")

if __name__ == "__main__":
    asyncio.run(main())