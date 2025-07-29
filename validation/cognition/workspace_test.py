#!/usr/bin/env python3
"""🧠 COGNITIVE WORKSPACE VALIDATION - Test the canonical ReAct architecture."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator


async def main():
    print("🧠 COGNITIVE WORKSPACE VALIDATION")
    print("=" * 40 + "\n")

    # Create agent - auto-detects available LLM from .env
    agent = Agent(
        name="workspace_tester",
        identity="cognitive assistant testing workspace fields",
        tools=[Calculator()],
        memory=False,
        depth=5,
        debug=True,  # Show cognitive workspace updates
        notify=True,
    )

    print("Testing cognitive workspace integration...")
    print("Expected: Beautiful dot notation (state.approach) instead of dict ceremony\n")

    # Test cognitive workspace evolution through multi-step reasoning
    query = "I need to calculate the area of a circle with radius 5, then find what percentage that is of a square with side length 12"

    print(f"🎯 Query: {query}\n")
    
    try:
        result = await agent.run(query)
        print(f"\n✅ Final Result: {result}")
        print("\n🎵 Cognitive workspace test complete!")
        
        # Test state access patterns
        if hasattr(agent, '_last_state') and agent._last_state:
            state = agent._last_state
            print(f"\n🧠 Final Workspace State:")
            print(f"   objective: {state.objective}")
            print(f"   understanding: {state.understanding}")  
            print(f"   approach: {state.approach}")
            print(f"   discoveries: {state.discoveries}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())