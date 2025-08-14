#!/usr/bin/env python3
"""Memory inspection - direct domain access for Claude debugging."""

import asyncio

from cogency.context.memory import Memory


async def main():
    """Inspect memory state and activation."""
    user_id = "default"

    print("=== MEMORY INSPECTION ===")

    # Create memory instance
    memory = Memory()

    # Test activation
    profile_context = await memory.activate(user_id)
    print(f"Memory activated: {profile_context is not None}")

    if profile_context:
        print(f"Profile length: {len(profile_context)} chars")
        print(f"Profile preview: {profile_context[:200]}...")
    else:
        print("No memory profile found")

    # Test memory operations if available
    if hasattr(memory, "get_profile"):
        profile = await memory.get_profile(user_id)
        print(f"Raw profile: {profile}")


if __name__ == "__main__":
    asyncio.run(main())
