#!/usr/bin/env python3
"""Show off BEAUTIFUL tracing - see exactly how the agent thinks."""
import asyncio
from cogency import Agent, CalculatorTool, WeatherTool

async def main():
    # Agent with tracing enabled
    agent = Agent("analyst", tools=[CalculatorTool(), WeatherTool()])
    
    print("🔍 TRACING DEMO - Watch the agent think step by step\n")
    
    # Run with tracing
    result = await agent.run("What's 15 * 23 and what's the weather in Tokyo?")
    
    print("\n" + "="*60)
    print("💡 FINAL RESULT:")
    print(result)
    
    print("\n" + "="*60) 
    print("🚀 EXECUTION TRACE:")
    if hasattr(agent, '_last_trace') and agent._last_trace:
        print(agent._last_trace)
    else:
        print("Tracing not available in this agent implementation")

if __name__ == "__main__":
    asyncio.run(main())