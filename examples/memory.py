#!/usr/bin/env python3
"""Memory tool isolation test - Smart memory behavior."""
import asyncio
from cogency import Agent, FSMemory

async def main():
    print("🧠 SMART MEMORY DEMONSTRATION")
    print("=" * 50)
    
    # Create agent with memory backend - recall tool auto-registered
    memory = FSMemory(memory_dir=".memory")
    agent = Agent("memory", memory=memory)
    
    # Call 1: Natural info storage - agent should auto-store
    print("📝 Sharing personal info (watch it get stored):")
    final_response_chunks = []
    async for chunk in agent.stream("I have ADHD and work as a software engineer in SF"):
        print(chunk, end="", flush=True)
        if "📝 " in chunk:
            final_response_chunks.append(chunk.split("📝 ", 1)[1])
    result1 = "".join(final_response_chunks)
    
    print(f"\n\n🔍 Testing recall (watch it remember):")
    final_response_chunks = []
    async for chunk in agent.stream("What do you know about my work situation?"):
        print(chunk, end="", flush=True)
        if "📝 " in chunk:
            final_response_chunks.append(chunk.split("📝 ", 1)[1])
    result2 = "".join(final_response_chunks)
    
    # Verify it's actually using memory, not hallucinating
    result_str = str(result2).lower()
    has_memory = any(word in result_str for word in ["adhd", "engineer", "sf", "san francisco"])
    assert has_memory, f"No memory recall: {result2}"
    print(f"\n\n✅ Memory working - found context: {has_memory}")

if __name__ == "__main__":
    asyncio.run(main())