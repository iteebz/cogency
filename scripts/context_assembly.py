#!/usr/bin/env python3
"""Context assembly debugging - inspect context building for Claude."""

import asyncio

from cogency.context.assembly import build_context
from cogency.context.conversation import Conversation


async def main():
    """Debug context assembly process."""
    print("=== CONTEXT ASSEMBLY DEBUG ===")

    # Test minimal context building
    context = await build_context(user_id="default", query="test query", iteration=1)

    print(f"Base context length: {len(context)} chars")
    print("Context sections:")

    sections = context.split("\n\n")
    for i, section in enumerate(sections, 1):
        if section.strip():
            header = section.split("\n")[0] if "\n" in section else section[:50]
            print(f"  {i}. {header}...")

    # Test with conversation
    print("\n--- With Conversation ---")
    conv = Conversation(
        user_id="default",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    )

    conv_context = await build_context(
        conversation=conv, user_id="default", query="follow up", iteration=2
    )

    print(f"With conversation length: {len(conv_context)} chars")

    if len(conv_context) > len(context):
        print("✅ Conversation context added successfully")
    else:
        print("⚠️ Conversation context may not be working")


if __name__ == "__main__":
    asyncio.run(main())
