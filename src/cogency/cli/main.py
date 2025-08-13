"""Main CLI entry point and argument parsing."""

import argparse
import asyncio
import sys

from .conversations import conversation_command
from .interactive import interactive_mode
from .knowledge import knowledge_command
from .memory import memory_command
from .setup import setup_agent

# Telemetry replaced by canonical logs command
from .tools import tools_command


def main():
    """CLI entry point."""
    # ULTRA-FAST EXIT - Handle --help and --version before any heavy imports
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""usage: cogency {ask,chat,conversation,tool,logs,knowledge,memory} ...

Cogency - Zero ceremony cognitive agents

commands:
  ask MESSAGE           One-shot query to agent
  chat                  Interactive conversation mode
  conversation          Conversation management (new, history, continue, search, archive)
  tool                  Tool diagnostics and management
  logs                  Execution logs and diagnostics

  TIER 2 POWER USER FEATURES:
  knowledge             Advanced knowledge management (search, stats, export, prune)
  memory                Advanced memory control (clear, show, export, stats)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

agent options:
  --tools TOOL_LIST     Comma-separated tools (default: Files,Shell,Search,Scrape,Recall)
  --memory              Enable conversation memory
  --debug               Enable debug mode with logs
  --retrieval-path PATH Path for Retrieve tool embeddings

examples:
  cogency ask "What is Python?"
  cogency ask "Help with code" --tools Files,Shell
  cogency chat --stream --tools Files,Search,Retrieve --retrieval-path ./docs
  cogency conversation new
  cogency conversation history --detailed
  cogency conversation search --query "python"
  cogency knowledge search "machine learning"
  cogency knowledge stats
  cogency memory show --raw
  cogency tool list
  cogency logs tool
  cogency logs --summary""")
        sys.exit(0)

    if "--version" in sys.argv:
        try:
            from importlib.metadata import version

            print(f"cogency {version('cogency')}")
        except Exception:
            print("cogency 1.3.0")  # Fallback
        sys.exit(0)

    # Parse constitutional CLI structure
    parser = argparse.ArgumentParser(description="Cogency - Zero ceremony cognitive agents")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ask - one-shot query (beautiful simplicity)
    ask_parser = subparsers.add_parser("ask", help="One-shot query to agent")
    ask_parser.add_argument("message", nargs="+", help="Your question or request")
    ask_parser.add_argument("--memory", action="store_true", help="Enable conversation memory")
    ask_parser.add_argument("--debug", action="store_true", help="Show debug information")
    ask_parser.add_argument(
        "--tools",
        default="Files,Shell,Search,Scrape,Recall",
        help="Comma-separated tool list (default: Files,Shell,Search,Scrape,Recall)",
    )
    ask_parser.add_argument(
        "--retrieval-path", help="Path to document embeddings for Retrieve tool"
    )

    # Chat - interactive mode (clear intent)
    chat_parser = subparsers.add_parser("chat", help="Interactive conversation mode")
    chat_parser.add_argument("--stream", action="store_true", help="Enable streaming responses")
    chat_parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with telemetry"
    )
    chat_parser.add_argument("--timing", action="store_true", help="Show timing metrics")
    chat_parser.add_argument(
        "--memory",
        action="store_true",
        default=True,
        help="Enable conversation memory (default: on)",
    )
    chat_parser.add_argument(
        "--tools",
        default="Files,Shell,Search,Scrape,Recall",
        help="Comma-separated tool list (default: Files,Shell,Search,Scrape,Recall)",
    )
    chat_parser.add_argument(
        "--retrieval-path", help="Path to document embeddings for Retrieve tool"
    )

    # Tool subcommand (canonical singular)
    tool_parser = subparsers.add_parser("tool", help="Tool diagnostics")
    tool_parser.add_argument("action", choices=["list", "inspect", "test", "benchmark", "validate"])
    tool_parser.add_argument("tool_name", nargs="?", help="Tool name for inspect/test")

    # Conversation subcommand (canonical conversation management)
    conversation_parser = subparsers.add_parser("conversation", help="Conversation management")
    conversation_parser.add_argument(
        "action",
        choices=["new", "history", "list", "continue", "current", "search", "filter", "archive"],
    )
    conversation_parser.add_argument(
        "--conversation-id", help="Conversation ID for continue/archive command"
    )
    conversation_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed history with content previews"
    )
    conversation_parser.add_argument("--search", help="Search conversations by keyword")
    conversation_parser.add_argument("--query", help="Search query for conversation search")
    conversation_parser.add_argument(
        "--filter", help="Filter conversations (today/week/month/long/short)"
    )

    # TIER 2 POWER USER FEATURES

    # Knowledge management subcommand
    knowledge_parser = subparsers.add_parser("knowledge", help="Advanced knowledge management")
    knowledge_parser.add_argument("action", choices=["search", "stats", "export", "prune"])
    knowledge_parser.add_argument("query", nargs="?", help="Search query for knowledge search")
    knowledge_parser.add_argument(
        "--format", choices=["json", "markdown"], default="json", help="Export format"
    )
    knowledge_parser.add_argument("--days", type=int, default=30, help="Days threshold for pruning")

    # Memory control subcommand
    memory_parser = subparsers.add_parser("memory", help="Advanced memory control")
    memory_parser.add_argument("action", choices=["clear", "show", "export", "stats"])
    memory_parser.add_argument(
        "conversation_id", nargs="?", help="Conversation ID for memory export"
    )
    memory_parser.add_argument("--raw", action="store_true", help="Show raw memory storage format")

    # Logs subcommand - canonical telemetry replacement
    logs_parser = subparsers.add_parser("logs", help="Show execution logs and diagnostics")
    logs_parser.add_argument(
        "filter", nargs="?", help="Filter by type: tool, error, memory, state, performance"
    )
    logs_parser.add_argument("--count", type=int, default=20, help="Number of recent events")
    logs_parser.add_argument(
        "--summary", action="store_true", help="Show session summary with event breakdown"
    )
    logs_parser.add_argument(
        "--debug", action="store_true", help="Include debug-level events (internal mechanics)"
    )

    args = parser.parse_args()

    # Handle missing command - show help
    if not args.command:
        parser.print_help()
        return

    # EARLY EXIT PATTERN - Handle subcommands that don't need Agent/providers
    if args.command == "tool":
        asyncio.run(tools_command(args.action, args.tool_name))
        return

    if args.command == "conversation":
        kwargs = {}
        if hasattr(args, "detailed") and args.detailed:
            kwargs["detailed"] = True
        if hasattr(args, "search") and args.search:
            kwargs["search"] = args.search
        if hasattr(args, "query") and args.query:
            kwargs["query"] = args.query
        if hasattr(args, "filter") and args.filter:
            kwargs["filter"] = args.filter
        asyncio.run(conversation_command(args.action, args.conversation_id, **kwargs))
        return

    if args.command == "knowledge":
        kwargs = {}
        if hasattr(args, "format"):
            kwargs["format"] = args.format
        if hasattr(args, "days"):
            kwargs["days"] = args.days
        asyncio.run(knowledge_command(args.action, args.query, **kwargs))
        return

    if args.command == "memory":
        kwargs = {}
        if hasattr(args, "raw") and args.raw:
            kwargs["raw"] = True
        asyncio.run(memory_command(args.action, args.conversation_id, **kwargs))
        return

    if args.command == "logs":
        from .logs import logs_command

        asyncio.run(logs_command(args.filter, args.count, args.summary, args.debug))
        return

    # Agent commands - setup agent using canonical implementation
    tool_names = getattr(args, "tools", "Files,Shell,Search,Scrape,Recall")
    memory_enabled = getattr(args, "memory", False)
    retrieval_path = getattr(args, "retrieval_path", None)

    agent = setup_agent(tool_names, memory_enabled, retrieval_path)

    # Execute command with clear intent
    if args.command == "ask":
        # One-shot mode - simple and fast with conversation continuity
        message = " ".join(args.message)

        async def ask_once():
            from cogency.cli_session import get_or_create_conversation_id, save_conversation_id

            # Get existing conversation_id for continuity
            conversation_id = await get_or_create_conversation_id()

            if args.debug:
                print(f"🔍 Query: {message}")
                if conversation_id:
                    print(f"📝 Continuing conversation: {conversation_id[:8]}...")
                else:
                    print("📝 Starting new conversation")

            # CANONICAL TUPLE RETURN PATTERN: Universal persistence contract
            response, final_conversation_id = await agent.run(
                message, "default", None, conversation_id
            )

            # Save conversation_id if new conversation was created
            if not conversation_id:
                await save_conversation_id(final_conversation_id, "default")
                if args.debug:
                    print(f"💾 Saved conversation: {final_conversation_id[:8]}...")

            print(response)

            if args.debug:
                print(f"\n📊 Memory enabled: {memory_enabled}")

        asyncio.run(ask_once())

    elif args.command == "chat":
        # Interactive mode - rich experience
        asyncio.run(
            interactive_mode(agent, stream=args.stream, debug=args.debug, timing=args.timing)
        )
