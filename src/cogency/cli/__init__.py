"""CLI interface for Cogency."""

import sys


def main():
    """CLI entry point."""

    # Show last conversation
    if len(sys.argv) > 1 and sys.argv[1] == "last":
        from .debug import show_conversation

        if len(sys.argv) > 2:
            show_conversation(sys.argv[2])
        else:
            show_conversation()
        return

    # Show exact LLM prompt
    if len(sys.argv) > 1 and sys.argv[1] == "prompt":
        from .debug import show_context

        if len(sys.argv) > 2:
            show_context(sys.argv[2])
        else:
            show_context()
        return

    # Database inspection
    if len(sys.argv) > 1 and sys.argv[1] == "db":
        from .debug import query_main

        query_main()
        return

    # Database statistics
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        from .admin import show_stats

        show_stats()
        return

    # User profiles
    if len(sys.argv) > 1 and sys.argv[1] == "users":
        from .admin import users_main

        users_main()
        return

    # Profile inspection
    if len(sys.argv) > 1 and sys.argv[1] == "profile":
        from ..context.profile import get

        user_id = "ask_user"  # Default CLI user
        user_profile = get(user_id)
        if user_profile:
            print("🧠 Current Profile:")
            print(f"  Who: {user_profile.get('who', 'Unknown')}")
            print(f"  Style: {user_profile.get('style', 'Unknown')}")
            print(f"  Focus: {user_profile.get('focus', 'Unknown')}")
            print(f"  History: {user_profile.get('history', 'None')}")
        else:
            print("📭 No profile found")
        return

    # Nuclear cleanup
    if len(sys.argv) > 1 and sys.argv[1] == "nuke":
        from .admin import nuke_everything

        nuke_everything()
        return

    # Help
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        print("🤖 Cogency - Streaming consciousness for AI agents")
        print()
        print("🚀 EXECUTION:")
        print(
            '  cogency "your question"              # Ask a question (continues previous conversation)'
        )
        print('  cogency "your question" --new        # Start fresh conversation (resets context)')
        print('  cogency "your question" --debug      # Show execution details')
        print('  cogency "your question" --show-stream # Show raw token stream')
        print()
        print("🔧 DEBUGGING:")
        print("  cogency last [conv_id]               # Show last conversation flow")
        print("  cogency prompt [conv_id]             # Show exact LLM prompt sent")
        print("  cogency db                           # Interactive database inspection")
        print("  cogency stats                        # Database health stats")
        print("  cogency profile                      # Show user memory profile")
        print()
        print("⚙️ OPTIONS:")
        print("  --llm=name              LLM provider (openai, gemini, anthropic)")
        print("  --mode=type             Stream mode (auto, resume, replay)")
        print("  --max-iterations=N      Maximum reasoning iterations (default: 3)")
        print("  --user=name             User identity for memory/context")
        print('  --instructions="..."    Custom agent instructions')
        print("  --no-tools              Disable all tools")
        print("  --no-profile            Disable user memory")
        print("  --no-sandbox            Disable security sandbox")
        print("  --new                   Force new conversation")
        print("  --debug                 Show execution traces")
        print("  --show-stream           Show raw token stream")
        print()
        print("💡 Example workflow:")
        print('  cogency "analyze this bug"           # Start debugging session')
        print('  cogency "try this solution"          # Continue in same conversation')
        print('  cogency "restart" --new              # Reset to a fresh conversation')
        print('  cogency "verify the fix" --debug     # See execution details')
        print("  cogency last                         # Review what happened")
        print("  cogency prompt                       # See exact LLM context")
        print()
        print("🗑️  ADMIN:")
        print("  cogency nuke                         # Delete all data")
        return

    # Default: agent execution
    import asyncio

    from .ask import main as ask_main

    asyncio.run(ask_main())


if __name__ == "__main__":
    main()
