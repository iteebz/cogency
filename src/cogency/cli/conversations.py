"""Conversation management commands - canonical CLI workflow completion."""

from typing import Optional

from cogency.cli_session import CLISession
from cogency.storage.sqlite import SQLite


async def conversation_command(subcommand: str, conversation_id: str = None, **kwargs):
    """Handle conversation management commands."""
    print("💬 Cogency Conversation Management")
    print("=" * 50)

    if subcommand == "new":
        await start_new_conversation()
    elif subcommand == "history":
        detailed = kwargs.get("detailed", False)
        search_query = kwargs.get("search")
        if search_query:
            await search_conversations(search_query)
        elif detailed:
            await detailed_history()
        else:
            await list_conversations()
    elif subcommand == "list":
        await list_conversations()
    elif subcommand == "continue":
        if not conversation_id:
            print("❌ Error: --conversation-id required for continue")
            return
        await continue_conversation(conversation_id)
    elif subcommand == "current":
        await show_current_conversation()
    elif subcommand == "search":
        search_query = kwargs.get("query")
        if not search_query:
            print("❌ Error: Search query required")
            print("Usage: cogency conversation search --query 'keyword'")
            return
        await search_conversations(search_query)
    elif subcommand == "filter":
        filter_type = kwargs.get("filter")
        await filter_conversations(filter_type)
    elif subcommand == "archive":
        if not conversation_id:
            print("❌ Error: conversation-id required for archive")
            print("Usage: cogency conversation archive <conv-id>")
            return
        await archive_conversation(conversation_id)
    else:
        print(f"❌ Unknown conversation action: {subcommand}")
        print("Available actions: new, history, list, continue, current, search, filter, archive")


async def start_new_conversation():
    """Start new conversation explicitly - clears current session."""
    session = CLISession()
    await session.clear_conversation()
    print("✨ Started new conversation")
    print("Next query will create fresh conversation context")


async def list_conversations(limit: int = 20):
    """List conversation history with titles."""
    store = SQLite()
    conversations = await store.list_conversations("default", limit)

    if not conversations:
        print("📭 No conversations found")
        return

    print(f"📋 Recent Conversations ({len(conversations)})")
    print("-" * 80)

    # Get current conversation for highlighting
    session = CLISession()
    current_id = await session.get_conversation_id()

    for i, conv in enumerate(conversations, 1):
        conv_id = conv["conversation_id"]
        title = conv["title"]
        message_count = conv["message_count"]
        updated_at = conv["updated_at"]

        # Highlight current conversation
        marker = "🔸" if conv_id == current_id else "  "

        # Format timestamp
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%m/%d %H:%M")
        except Exception:
            time_str = updated_at[:16]

        print(f"{marker} {i:2}. {conv_id[:8]}... | {message_count:2} msgs | {time_str} | {title}")


async def continue_conversation(conversation_id: str):
    """Resume specific conversation by ID."""
    store = SQLite()

    # Support partial ID matching - get all conversations first
    conversations = await store.list_conversations("default", 100)

    # Find conversation by full ID or partial match
    target_conversation = None
    if len(conversation_id) >= 8:  # Partial ID matching
        matches = [c for c in conversations if c["conversation_id"].startswith(conversation_id)]
        if len(matches) == 1:
            target_conversation = matches[0]
        elif len(matches) > 1:
            print(f"❌ Ambiguous ID '{conversation_id}' matches {len(matches)} conversations")
            for match in matches[:5]:  # Show first 5 matches
                print(f"   {match['conversation_id'][:8]}... - {match['title']}")
            return

    if not target_conversation:
        print(f"❌ Conversation {conversation_id[:8]}... not found")
        return

    full_conversation_id = target_conversation["conversation_id"]

    # Load full conversation to validate
    conversation = await store.load_conversation(full_conversation_id, "default")
    if not conversation:
        print(f"❌ Conversation {full_conversation_id[:8]}... data corrupted")
        return

    # Set as current conversation
    session = CLISession()
    await session.save_conversation_id(full_conversation_id)

    # Get conversation metadata
    title = target_conversation["title"]

    print(f"📝 Resumed conversation: {full_conversation_id[:8]}...")
    print(f"📋 Title: {title}")
    print(f"💬 Messages: {len(conversation.messages)}")


async def show_current_conversation():
    """Show currently active conversation."""
    session = CLISession()
    current_id = await session.get_conversation_id()

    if not current_id:
        print("📝 No active conversation")
        print("Next query will create new conversation")
        return

    # Get conversation details
    store = SQLite()
    conversation = await store.load_conversation(current_id, "default")

    if not conversation:
        print(f"⚠️  Active conversation {current_id[:8]}... not found in storage")
        print("Run 'cogency new' to start fresh")
        return

    # Get conversation metadata
    conversations = await store.list_conversations("default", 100)
    conv_data = next((c for c in conversations if c["conversation_id"] == current_id), None)
    title = conv_data["title"] if conv_data else "Unknown"

    print("📝 Current Conversation")
    print("-" * 30)
    print(f"ID: {current_id[:8]}...")
    print(f"Title: {title}")
    print(f"Messages: {len(conversation.messages)}")

    if conversation.messages:
        last_msg = conversation.messages[-1]
        last_content = last_msg.get("content", "")
        if len(last_content) > 100:
            last_content = last_content[:97] + "..."
        print(f"Last: {last_content}")


def find_conversation_by_prefix(conversations: list[dict], prefix: str) -> Optional[dict]:
    """Find conversation by ID prefix - helper for fuzzy matching."""
    matches = [c for c in conversations if c["conversation_id"].startswith(prefix)]
    return matches[0] if len(matches) == 1 else None


# TIER 2 ADVANCED CONVERSATION MANAGEMENT FEATURES


async def detailed_history(user_id: str = "default", limit: int = 10):
    """Show detailed conversation history with metadata and content previews."""
    store = SQLite()
    conversations = await store.list_conversations(user_id, limit)

    if not conversations:
        print("📭 No conversations found")
        return

    print(f"📋 Detailed Conversation History ({len(conversations)})")
    print("=" * 80)

    # Get current conversation for highlighting
    session = CLISession()
    current_id = await session.get_conversation_id()

    for i, conv in enumerate(conversations, 1):
        conv_id = conv["conversation_id"]
        title = conv["title"]
        message_count = conv["message_count"]
        updated_at = conv["updated_at"]

        # Load full conversation for details
        full_conv = await store.load_conversation(conv_id, user_id)

        # Highlight current conversation
        marker = "🔸" if conv_id == current_id else "  "

        # Format timestamp
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_str = updated_at[:19]

        print(f"\n{marker} {i}. CONVERSATION {conv_id[:8]}...")
        print(f"    📝 Title: {title}")
        print(f"    💬 Messages: {message_count}")
        print(f"    📅 Updated: {time_str}")

        if full_conv and full_conv.messages:
            # Show first and last message preview
            first_msg = full_conv.messages[0]
            last_msg = full_conv.messages[-1]

            if first_msg.get("role") == "user":
                first_content = first_msg.get("content", "")[:100]
                print(
                    f"    🗣️  First: {first_content}{'...' if len(first_msg.get('content', '')) > 100 else ''}"
                )

            if len(full_conv.messages) > 1 and last_msg.get("role") == "assistant":
                last_content = last_msg.get("content", "")[:100]
                print(
                    f"    🤖 Last: {last_content}{'...' if len(last_msg.get('content', '')) > 100 else ''}"
                )


async def search_conversations(query: str, user_id: str = "default", limit: int = 50):
    """Search conversations by content with keyword matching."""
    store = SQLite()
    conversations = await store.list_conversations(user_id, limit)

    if not conversations:
        print("📭 No conversations to search")
        return

    print(f"🔍 Searching conversations for: '{query}'")
    print("-" * 60)

    matches = []
    query_lower = query.lower()

    for conv in conversations:
        conv_id = conv["conversation_id"]
        title = conv["title"]

        # Check title first
        title_match = query_lower in title.lower()
        content_matches = []

        # Load full conversation to search content
        full_conv = await store.load_conversation(conv_id, user_id)
        if full_conv and full_conv.messages:
            for i, msg in enumerate(full_conv.messages):
                content = msg.get("content", "")
                if query_lower in content.lower():
                    # Find the matching snippet
                    content_lower = content.lower()
                    match_pos = content_lower.find(query_lower)

                    # Extract context around match
                    start = max(0, match_pos - 50)
                    end = min(len(content), match_pos + len(query) + 50)
                    snippet = content[start:end]

                    content_matches.append(
                        {
                            "message_index": i,
                            "role": msg.get("role", "unknown"),
                            "snippet": snippet,
                            "match_pos": match_pos,
                        }
                    )

        if title_match or content_matches:
            matches.append(
                {
                    "conversation": conv,
                    "title_match": title_match,
                    "content_matches": content_matches,
                }
            )

    if not matches:
        print(f"❌ No conversations found containing '{query}'")
        return

    print(f"✅ Found {len(matches)} conversations with matches")
    print()

    for i, match in enumerate(matches, 1):
        conv = match["conversation"]
        conv_id = conv["conversation_id"]
        title = conv["title"]

        print(f"{i:2}. {conv_id[:8]}... | {conv['message_count']} msgs | {title}")

        if match["title_match"]:
            print("     📝 Title match")

        if match["content_matches"]:
            print(f"     💬 {len(match['content_matches'])} content match(es):")
            for _j, content_match in enumerate(match["content_matches"][:3]):  # Show first 3
                role_icon = "🗣️" if content_match["role"] == "user" else "🤖"
                snippet = content_match["snippet"].replace("\n", " ").strip()
                print(f"       {role_icon} ...{snippet}...")

            if len(match["content_matches"]) > 3:
                print(f"       ... and {len(match['content_matches']) - 3} more matches")

        print()


async def filter_conversations(filter_type: str = None, user_id: str = "default"):
    """Filter conversations by user, date, topic, or other criteria."""
    store = SQLite()

    if not filter_type:
        print("Available filters:")
        print("  user - Filter by user ID")
        print("  today - Conversations from today")
        print("  week - Conversations from this week")
        print("  month - Conversations from this month")
        print("  long - Conversations with 10+ messages")
        print("  short - Conversations with <5 messages")
        return

    conversations = await store.list_conversations(user_id, 100)

    if not conversations:
        print("📭 No conversations found")
        return

    filtered = []

    if filter_type == "user":
        # For now, all conversations are from same user
        filtered = conversations
        filter_desc = f"user '{user_id}'"

    elif filter_type == "today":
        from datetime import datetime, timedelta

        today = datetime.now().date()
        for conv in conversations:
            try:
                conv_date = datetime.fromisoformat(conv["updated_at"].replace("Z", "+00:00")).date()
                if conv_date == today:
                    filtered.append(conv)
            except Exception:
                continue
        filter_desc = "today"

    elif filter_type == "week":
        from datetime import datetime, timedelta

        week_ago = datetime.now() - timedelta(days=7)
        for conv in conversations:
            try:
                conv_date = datetime.fromisoformat(conv["updated_at"].replace("Z", "+00:00"))
                if conv_date >= week_ago:
                    filtered.append(conv)
            except Exception:
                continue
        filter_desc = "this week"

    elif filter_type == "month":
        from datetime import datetime, timedelta

        month_ago = datetime.now() - timedelta(days=30)
        for conv in conversations:
            try:
                conv_date = datetime.fromisoformat(conv["updated_at"].replace("Z", "+00:00"))
                if conv_date >= month_ago:
                    filtered.append(conv)
            except Exception:
                continue
        filter_desc = "this month"

    elif filter_type == "long":
        filtered = [conv for conv in conversations if conv["message_count"] >= 10]
        filter_desc = "long conversations (10+ messages)"

    elif filter_type == "short":
        filtered = [conv for conv in conversations if conv["message_count"] < 5]
        filter_desc = "short conversations (<5 messages)"

    else:
        print(f"❌ Unknown filter type: {filter_type}")
        return

    print(f"🔽 Conversations filtered by {filter_desc}")
    print(f"📊 {len(filtered)} of {len(conversations)} conversations match")
    print("-" * 60)

    if not filtered:
        print("📭 No conversations match the filter criteria")
        return

    # Display filtered conversations
    session = CLISession()
    current_id = await session.get_conversation_id()

    for i, conv in enumerate(filtered, 1):
        conv_id = conv["conversation_id"]
        title = conv["title"]
        message_count = conv["message_count"]
        updated_at = conv["updated_at"]

        marker = "🔸" if conv_id == current_id else "  "

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%m/%d %H:%M")
        except Exception:
            time_str = updated_at[:16]

        print(f"{marker} {i:2}. {conv_id[:8]}... | {message_count:2} msgs | {time_str} | {title}")


async def archive_conversation(conversation_id: str, user_id: str = "default"):
    """Archive conversation (mark as archived/inactive)."""
    store = SQLite()

    # Find conversation with partial ID support
    conversations = await store.list_conversations(user_id, 100)
    target_conversation = None

    if len(conversation_id) >= 8:
        matches = [c for c in conversations if c["conversation_id"].startswith(conversation_id)]
        if len(matches) == 1:
            target_conversation = matches[0]
        elif len(matches) > 1:
            print(f"❌ Ambiguous ID '{conversation_id}' matches {len(matches)} conversations")
            for match in matches[:5]:
                print(f"   {match['conversation_id'][:8]}... - {match['title']}")
            return

    if not target_conversation:
        print(f"❌ Conversation {conversation_id[:8]}... not found")
        return

    full_conversation_id = target_conversation["conversation_id"]
    title = target_conversation["title"]

    print(f"📦 Archiving conversation: {full_conversation_id[:8]}...")
    print(f"📋 Title: {title}")
    print(f"💬 Messages: {target_conversation['message_count']}")
    print()

    response = (
        input("❓ Confirm archive? This will remove from active history (y/N): ").strip().lower()
    )

    if response != "y":
        print("❌ Archive cancelled")
        return

    # TODO: Implement actual archiving mechanism
    # For now, this would be a soft delete or marking as archived
    # success = await store.archive_conversation(full_conversation_id)

    print("⚠️  Note: Archiving not yet implemented - this was a preview")
    print("✅ Would archive conversation successfully")

    # If this was the current conversation, clear it
    session = CLISession()
    current_id = await session.get_conversation_id()
    if current_id == full_conversation_id:
        await session.clear_conversation()
        print("🔄 Cleared as current conversation")
