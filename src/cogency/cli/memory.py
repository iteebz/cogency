"""Advanced memory control commands - TIER 2 power user utilities."""

import json
from datetime import datetime
from typing import Optional

from cogency.memory import Memory
from cogency.storage.sqlite import SQLite


async def memory_command(action: str, conversation_id: Optional[str] = None, **kwargs):
    """Handle memory management commands."""
    print("🔄 Cogency Memory Control")
    print("=" * 50)

    if action == "clear":
        await clear_memory()
    elif action == "show":
        raw = kwargs.get("raw", False)
        await show_memory(raw)
    elif action == "export":
        if not conversation_id:
            print("❌ Error: --conversation-id required for export")
            print("Usage: cogency memory export <conv-id>")
            return
        await export_memory(conversation_id)
    elif action == "stats":
        await memory_stats()
    else:
        print(f"❌ Unknown memory action: {action}")
        print("Available actions: clear, show, export, stats")


async def clear_memory(user_id: str = "default"):
    """Clear current memory context injection."""
    print("🧹 Clearing memory context")
    print("-" * 30)

    try:
        # Get current memory system
        memory = Memory()

        # Clear runtime memory state
        if hasattr(memory._system, "_profiles"):
            if user_id in memory._system._profiles:
                del memory._system._profiles[user_id]
                print(f"✅ Cleared runtime profile for user: {user_id}")
            else:
                print(f"📭 No runtime profile found for user: {user_id}")

        # Show what would be cleared from persistent storage
        store = SQLite()
        profile = await store.load_profile(f"{user_id}:default")

        if profile:
            print("⚠️  Persistent profile data found:")
            context = profile.context()
            if context:
                lines = context.split("\n")
                for line in lines[:5]:  # Show first 5 lines
                    print(f"    {line}")
                if len(lines) > 5:
                    print(f"    ... and {len(lines) - 5} more lines")

            print("\n❓ Also clear persistent profile? (y/N): ", end="")
            try:
                response = input().strip().lower()
                if response == "y":
                    # TODO: Implement profile deletion
                    print("⚠️  Persistent profile clearing not yet implemented")
                    print("Runtime memory cleared successfully")
                else:
                    print("✅ Runtime memory cleared, persistent profile preserved")
            except (EOFError, KeyboardInterrupt):
                print("\n✅ Runtime memory cleared, persistent profile preserved")
        else:
            print("✅ Memory context cleared successfully")

    except Exception as e:
        print(f"❌ Memory clear failed: {str(e)}")


async def show_memory(raw: bool = False, user_id: str = "default"):
    """Show current memory state and storage format."""
    print("👁️  Current Memory State")
    print("-" * 30)

    try:
        # Load memory system
        memory = Memory()
        store = SQLite()

        # Show runtime memory state
        print("🏃 Runtime Memory:")
        if hasattr(memory._system, "_profiles") and user_id in memory._system._profiles:
            profile = memory._system._profiles[user_id]
            context = profile.context()
            if context:
                print("  Active context injection:")
                for line in context.split("\n"):
                    print(f"    {line}")
            else:
                print("  No active context")
        else:
            print("  No runtime profile loaded")

        print()

        # Show persistent memory state
        print("💾 Persistent Memory:")
        profile = await store.load_profile(f"{user_id}:default")

        if not profile:
            print("  No persistent profile found")
            print("  Memory is created during conversations with --memory enabled")
            return

        if raw:
            # Show raw storage format
            print("📋 Raw Storage Format:")
            print("-" * 25)

            from dataclasses import asdict

            profile_dict = asdict(profile)

            # Format timestamps for readability
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()

            print(json.dumps(profile_dict, indent=2))
        else:
            # Show formatted memory content
            print("📝 Memory Content:")
            context = profile.context()
            if context:
                for line in context.split("\n"):
                    print(f"  {line}")
            else:
                print("  Profile exists but no context generated")

            # Show profile metadata
            print("\n📊 Profile Metadata:")
            print(f"  User ID: {profile.user_id}")
            print(f"  Created: {profile.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Updated: {profile.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Preferences: {len(profile.preferences)} items")
            print(f"  Goals: {len(profile.goals)} items")
            print(f"  Expertise areas: {len(profile.expertise_areas)} items")
            print(f"  Projects: {len(profile.projects)} items")

    except Exception as e:
        print(f"❌ Memory show failed: {str(e)}")


async def export_memory(conversation_id: str, user_id: str = "default"):
    """Export conversation memory to file."""
    print(f"📤 Exporting conversation memory: {conversation_id[:8]}...")
    print("-" * 60)

    try:
        store = SQLite()

        # Load conversation
        conversation = await store.load_conversation(conversation_id, user_id)
        if not conversation:
            print(f"❌ Conversation {conversation_id[:8]}... not found")
            return

        # Load user profile at time of conversation
        profile = await store.load_profile(f"{user_id}:default")

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cogency_memory_{conversation_id[:8]}_{timestamp}.json"

        # Prepare export data
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "user_id": user_id,
            "conversation": {
                "messages": conversation.messages,
                "last_updated": conversation.last_updated.isoformat(),
            },
        }

        if profile:
            from dataclasses import asdict

            profile_dict = asdict(profile)
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()
            export_data["user_profile"] = profile_dict
            export_data["memory_context"] = profile.context()
        else:
            export_data["user_profile"] = None
            export_data["memory_context"] = None

        # Write export file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print("✅ Memory exported successfully")
        print(f"📁 File: {filename}")
        print(f"💬 Messages: {len(conversation.messages)}")

        if profile:
            print(f"👤 Profile: {len(profile.preferences)} preferences, {len(profile.goals)} goals")
        else:
            print("👤 Profile: No persistent profile found")

    except Exception as e:
        print(f"❌ Memory export failed: {str(e)}")


async def memory_stats(user_id: str = "default"):
    """Display memory usage and optimization statistics."""
    print("📊 Memory System Statistics")
    print("-" * 35)

    try:
        store = SQLite()

        # Load user profile
        profile = await store.load_profile(f"{user_id}:default")

        if not profile:
            print("📭 No memory profile found")
            print("Memory is created during conversations with --memory enabled")
            return

        # Calculate profile statistics
        context = profile.context()
        context_lines = len(context.split("\n")) if context else 0
        context_chars = len(context) if context else 0

        # Age calculation
        age = datetime.now() - profile.created_at
        last_update_age = datetime.now() - profile.last_updated

        print("👤 Profile Statistics:")
        print(f"  User ID: {profile.user_id}")
        print(f"  Profile age: {age.days} days")
        print(f"  Last updated: {last_update_age.days} days ago")
        print()

        print("📏 Memory Size:")
        print(f"  Context lines: {context_lines}")
        print(f"  Context chars: {context_chars}")
        print(f"  Preferences: {len(profile.preferences)} items")
        print(f"  Goals: {len(profile.goals)} items")
        print(f"  Expertise areas: {len(profile.expertise_areas)} items")
        print(f"  Projects: {len(profile.projects)} items")
        print()

        # Memory efficiency metrics
        if context_chars > 0:
            min(100, max(0, 100 - (context_chars / 10)))  # Rough efficiency score
            print("⚡ Memory Efficiency:")
            print(f"  Context injection size: {context_chars} chars")
            if context_chars < 500:
                print("  Status: ✅ Optimal (minimal context)")
            elif context_chars < 1000:
                print("  Status: 🟡 Good (moderate context)")
            else:
                print("  Status: 🟠 Large (consider pruning)")
            print()

        # Show most recent content samples
        if profile.preferences:
            print("🔍 Recent Preferences:")
            prefs_items = list(profile.preferences.items())[-3:]
            for key, value in prefs_items:
                print(f"  {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
            print()

        if profile.goals:
            print("🎯 Current Goals:")
            for goal in profile.goals[-3:]:
                print(f"  • {goal}")
            print()

        # Memory optimization suggestions
        print("💡 Optimization Suggestions:")
        suggestions = []

        if len(profile.goals) > 10:
            suggestions.append(
                f"Consider pruning old goals ({len(profile.goals)} currently stored)"
            )

        if len(profile.preferences) > 20:
            suggestions.append(
                f"Large preference set ({len(profile.preferences)} items) - consider cleanup"
            )

        if context_chars > 1500:
            suggestions.append("Context injection is large - may impact performance")

        if last_update_age.days > 30:
            suggestions.append("Profile not updated recently - may contain stale information")

        if not suggestions:
            suggestions.append("✅ Memory profile is well-optimized")

        for suggestion in suggestions:
            print(f"  • {suggestion}")

    except Exception as e:
        print(f"❌ Memory stats failed: {str(e)}")
