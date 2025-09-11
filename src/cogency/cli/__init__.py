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

    # Show assembled context
    if len(sys.argv) > 1 and sys.argv[1] == "context":
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
            import json

            print(json.dumps(user_profile))
        else:
            print("{}")
        return

    # Nuclear cleanup
    if len(sys.argv) > 1 and sys.argv[1] == "nuke":
        # Handle nuke subcommands
        if len(sys.argv) > 2:
            subcommand = sys.argv[2]
            if subcommand == "sandbox":
                from .admin import nuke_sandbox

                nuke_sandbox()
                return
            if subcommand == "db":
                from .admin import nuke_db

                nuke_db()
                return
            return
            return
        # Default nuke with confirmation
        from .admin import nuke_everything

        nuke_everything()
        return

    # Help for Claude
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        print("Cogency - Streaming agents")
        print()
        print("EXECUTION:")
        print('  cogency "question"              # Ask (continues conversation)')
        print('  cogency "question" --new        # Start fresh conversation')
        print('  cogency "question" --debug      # Show execution details')
        print()
        print("DEBUGGING:")
        print("  cogency last [conv_id]          # Show conversation flow")
        print("  cogency context [conv_id]       # Show assembled context")
        print("  cogency db                      # Database inspection")
        print("  cogency stats                   # Database stats")
        print("  cogency profile                 # Show user profile")
        print()
        print("OPTIONS:")
        print("  --llm=name              LLM provider (openai, gemini, anthropic)")
        print("  --mode=type             Stream mode (auto, resume, replay)")
        print("  --max-iterations=N      Maximum reasoning iterations")
        print("  --user=name             User identity")
        print('  --instructions="..."    Custom agent instructions')
        print("  --no-tools              Disable tools")
        print("  --no-profile            Disable user memory")
        print("  --no-sandbox            Disable security sandbox")
        print("  --debug                 Show execution traces")
        print()
        print("ADMIN:")
        print("  cogency nuke                    # Delete all data")
        print("  cogency nuke sandbox            # Delete sandbox only")
        print("  cogency nuke db                 # Delete database only")
        return

    # Default: agent execution
    import asyncio

    from .ask import main as ask_main

    asyncio.run(ask_main())


if __name__ == "__main__":
    main()
