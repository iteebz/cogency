#!/usr/bin/env python3
"""Conversation debugging - direct domain access for Claude."""

import asyncio

from cogency.storage.sqlite.conversations import list_conversations, load_conversation


async def main():
    """Debug conversation storage and retrieval."""
    user_id = "default"

    print("=== CONVERSATION DEBUG ===")

    # List conversations
    conversations = await list_conversations(user_id, 20)
    print(f"Total conversations: {len(conversations)}")

    for i, conv in enumerate(conversations[:5], 1):
        conv_id = conv["conversation_id"]
        title = conv["title"]
        msg_count = conv["message_count"]
        print(f"{i}. {conv_id[:8]}... | {msg_count} msgs | {title}")

        # Load full conversation for first one
        if i == 1:
            full_conv = await load_conversation(conv_id, user_id)
            if full_conv and full_conv.messages:
                print(f"   Messages: {len(full_conv.messages)}")
                if full_conv.messages:
                    first_msg = full_conv.messages[0]
                    print(f"   First: {first_msg.get('content', '')[:80]}...")


if __name__ == "__main__":
    asyncio.run(main())
