#!/usr/bin/env python3
"""Smoke test for memory system - minimal chat test."""

import asyncio

# Set environment to use the current source
import sys
from pathlib import Path

sys.path.insert(0, "src")

from cogency import Agent


async def smoke_test():
    """Test memory system with simple conversation."""
    print("🧪 MEMORY SMOKE TEST - NO TOOLS")
    print("=" * 40)

    # Clear any existing memory first
    memory_dir = Path.home() / ".cogency" / "memory"
    test_file = memory_dir / "smoke_test.json"
    if test_file.exists():
        test_file.unlink()
        print("✅ Cleared existing memory")

    # Create agent without tools
    agent = Agent(tools=[])

    # First interaction - should establish baseline memory
    print("\n🗣️  FIRST INTERACTION:")
    query1 = "Hi, I'm John. I'm working on a Python web scraping project using BeautifulSoup"
    result1 = await agent(query1, user_id="smoke_test")
    print(f"Response: {result1.response[:100]}...")
    print(f"Conversation ID: {result1.conversation_id}")

    # Check if memory file was created
    if test_file.exists():
        import json

        with open(test_file) as f:
            memory = json.load(f)
        print(f"✅ Memory created: {memory}")
    else:
        print("❌ No memory file created")

    # Second interaction - should reference learned info
    print("\n🗣️  SECOND INTERACTION:")
    query2 = "What do you remember about my current project?"
    result2 = await agent(query2, user_id="smoke_test", conversation_id=result1.conversation_id)
    print(f"Response: {result2.response[:100]}...")

    # Check if memory was referenced
    contains_context = any(
        keyword in result2.response.lower()
        for keyword in ["john", "python", "scraping", "beautifulsoup"]
    )

    if contains_context:
        print("✅ Memory context successfully referenced")
    else:
        print("❌ Memory context not found in response")
        print(f"Full response: {result2.response}")

    # Final memory check
    if test_file.exists():
        with open(test_file) as f:
            final_memory = json.load(f)
        print(f"\n📝 Final memory state: {json.dumps(final_memory, indent=2)}")

    return contains_context


if __name__ == "__main__":
    success = asyncio.run(smoke_test())
    print(f"\n🎯 SMOKE TEST {'PASSED' if success else 'FAILED'}")
