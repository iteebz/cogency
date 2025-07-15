#!/usr/bin/env python3
"""Memory tool isolation test - Smart memory behavior."""
import asyncio
from cogency import Agent

async def main():
    print("🧠 Testing Smart Memory...")
    agent = Agent("memory")  # Auto-detects memory tools
    
    # Call 1: Natural info storage - agent should auto-store
    print("📝 Natural info sharing...")
    result1 = await agent.run("I have ADHD and work as a software engineer in SF", mode="summary")
    print(f"Storage: {result1}")
    
    # Call 2: Natural recall - agent should auto-recall
    print("🔍 Natural recall...")
    result2 = await agent.run("What do you know about my work situation?", mode="summary")
    print(f"Recall: {result2}")
    
    # Verify it's actually using memory, not hallucinating
    result_str = str(result2).lower()
    has_memory = any(word in result_str for word in ["adhd", "engineer", "sf", "san francisco"])
    assert has_memory, f"No memory recall: {result2}"

if __name__ == "__main__":
    asyncio.run(main())