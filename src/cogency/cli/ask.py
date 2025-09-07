#!/usr/bin/env python3
"""Cogency CLI - agent execution."""

import argparse
import asyncio
import sqlite3
import sys
import warnings

from .. import Agent
from ..lib.storage import get_db_path
from ..tools import TOOLS

# Suppress asyncio warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")

# Load environment variables
try:
    from dotenv import load_dotenv

    # Use override=True to ensure .env values replace empty environment variables
    load_dotenv(override=True)
except ImportError:
    pass


def get_last_conversation_id(user_id: str) -> str:
    """Get the last conversation ID for continuation, or create new one."""
    db_path = get_db_path()

    if not db_path.exists():
        # No database yet - create first conversation
        import uuid

        return str(uuid.uuid4())

    try:
        with sqlite3.connect(db_path) as db:
            result = db.execute(
                "SELECT conversation_id FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
                (user_id,),
            ).fetchone()

            if result:
                return result[0]  # Continue last conversation
            # No conversations for this user - create first one
            import uuid

            return str(uuid.uuid4())

    except Exception:
        # Database error - create new conversation
        import uuid

        return str(uuid.uuid4())


async def main():
    # Let __init__.py handle the no-arguments case
    if len(sys.argv) < 2:
        from . import main as cli_main

        cli_main()
        return

    # Parse arguments with argparse
    parser = argparse.ArgumentParser(description="Cogency Agent CLI")
    parser.add_argument("question", help="Question for the agent")
    parser.add_argument("--llm", default="gemini", choices=["openai", "gemini", "anthropic"])
    parser.add_argument("--mode", default="auto", choices=["auto", "resume", "replay"])
    parser.add_argument("--user", default="ask_user", help="User identity")
    parser.add_argument("--instructions", help="Custom agent instructions")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max iterations")
    parser.add_argument("--no-tools", action="store_true", help="Disable tools")
    parser.add_argument("--no-profile", action="store_true", help="Disable user memory")
    parser.add_argument("--no-sandbox", action="store_true", help="Disable security sandbox")
    parser.add_argument("--new", action="store_true", help="Force new conversation")
    parser.add_argument("--debug", action="store_true", help="Show execution traces")
    parser.add_argument("--show-stream", action="store_true", help="Show raw token stream")
    parser.add_argument("--metrics", action="store_true", help="Show token usage metrics")
    parser.add_argument("--verbose", action="store_true", help="Show detailed debug events")

    args = parser.parse_args()

    if args.debug:
        from ..lib.logger import logger

        logger.set_debug(True)

    # Create agent
    agent = Agent(
        llm=args.llm,
        tools=TOOLS if not args.no_tools else None,
        instructions=args.instructions,
        mode=args.mode,
        max_iterations=args.max_iterations,
        profile=not args.no_profile,
        sandbox=not args.no_sandbox,
    )

    # Continuation logic
    if args.new:
        import uuid

        conversation_id = str(uuid.uuid4())
        context_type = "fresh"
    else:
        conversation_id = get_last_conversation_id(args.user)
        context_type = "continue"

    # Show clean execution header
    config_parts = [args.llm, args.mode]
    if args.no_tools:
        config_parts.append("no tools")
    if args.no_profile:
        config_parts.append("no profile")
    if args.instructions:
        config_parts.append("custom instructions")

    print(f"🤖 Cogency Agent ({', '.join(config_parts)}, max_iterations={args.max_iterations})")
    print(f"👤 User: {args.user}")
    print(f"🔄 Context: {context_type}")
    print(f"❓ Question: {args.question}")
    # Clean session display
    session_name = f"session_{len(conversation_id) % 100:02d}"
    print(f"🆔 Session: {session_name}")
    print("─" * 50)

    # Debug mode - show assembled context
    if args.debug:
        from ..context import context

        print("🔍 DEBUG MODE: Assembled Context")
        print("=" * 60)
        messages = context.assemble(args.question, args.user, conversation_id, agent.config)
        for msg in messages:
            print(f"[{msg['role'].upper()}] {msg['content']}")
        print("=" * 60)

    try:
        # Streaming execution with observation
        from ..lib.observe import observe
        from .display import Renderer

        @observe(agent)
        async def observed_stream():
            async for event in agent.stream(
                args.question, user_id=args.user, conversation_id=conversation_id
            ):
                yield event

        # Create single stream instance
        stream_instance = observed_stream()

        renderer = Renderer(show_stream=args.show_stream, verbose=args.verbose)
        await renderer.render_stream(stream_instance)

        # Show metrics after stream completion
        if args.metrics and hasattr(observed_stream, "metrics"):
            metrics = observed_stream.metrics
            renderer.show_metrics(metrics)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
