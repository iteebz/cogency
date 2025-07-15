#!/usr/bin/env python3
"""MEMORY CAPABILITIES - Test agent persistence across conversations."""
import asyncio
from cogency import Agent

async def main():
    # Agent with memory enabled (auto-detects memory tools)
    agent = Agent("memory_assistant")

    print("🧠 TESTING MEMORY CAPABILITIES")
    print("=" * 50)

    # Store some information
    print("📝 STORING INFORMATION...")
    result1 = await agent.run("Remember that my favorite color is blue and I work as a software engineer.")
    print(f"Storage result: {result1}")
    print()

    # Store more complex info
    print("📝 STORING COMPLEX INFORMATION...")
    result2 = await agent.run("Also remember my project preferences: I like Python over JavaScript, prefer functional programming, and my current project is called 'Cogency' - an AI reasoning framework.")
    print(f"Complex storage result: {result2}")
    print()

    # Test recall
    print("🔍 TESTING RECALL...")
    result3 = await agent.run("What's my favorite color?")
    print(f"Color recall: {result3}")
    print()

    # Test complex recall
    print("🔍 TESTING COMPLEX RECALL...")
    result4 = await agent.run("What programming preferences do I have?")
    print(f"Preferences recall: {result4}")
    print()

    # Test memory-based reasoning
    print("🧠 TESTING MEMORY-BASED REASONING...")
    result5 = await agent.run("Based on what you know about me, would I prefer React or Vue.js for a new project?")
    print(f"Reasoning result: {result5}")
    
    print("\n" + "=" * 50)
    print("✅ Memory capabilities test complete!")

if __name__ == "__main__":
    asyncio.run(main())