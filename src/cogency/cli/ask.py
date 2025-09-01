#!/usr/bin/env python3
"""Cogency CLI - zero ceremony agent execution.

USAGE:
    cogency "your question"                    # Continue conversation (auto-context)
    cogency "your question" --new              # Force new conversation
    cogency "your question" --debug            # Show execution details
    cogency "your question" --show-stream      # Show raw token stream

PHILOSOPHY:
    - Continue context by default (Claude workflow)
    - Explicit --new when fresh context needed
    - Stream debugging when execution hangs
    - Zero ceremony, maximum utility
"""

import asyncio
import sys

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import sqlite3

from .. import Agent
from ..lib.storage import get_db_path
from ..tools import TOOLS


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
    if len(sys.argv) < 2:
        print("Usage: cogency 'your question here' [options]")
        print()
        print("💡 Examples:")
        print("  cogency 'analyze this bug'           # Continue debugging session")
        print("  cogency 'try this solution'          # Continue same context")
        print("  cogency 'new topic' --new            # Force fresh conversation")
        print("  cogency 'debug issue' --debug        # Show execution details")
        print("  cogency 'stuck query' --show-stream  # Show raw token stream")
        return

    # Parse arguments
    question = sys.argv[1]

    # Defaults
    llm = "gemini"
    mode = "auto"
    user_id = "ask_user"
    instructions = None
    max_iterations = 3
    use_tools = True
    profile = True
    sandbox = True
    debug = False
    show_stream = False
    force_new = False

    for arg in sys.argv[2:]:
        if arg == "--no-tools":
            use_tools = False
        elif arg == "--no-profile":
            profile = False
        elif arg == "--no-sandbox":
            sandbox = False
        elif arg == "--debug":
            debug = True
            from ..lib.logger import logger

            logger.set_debug(True)
        elif arg == "--show-stream":
            show_stream = True
        elif arg == "--new":
            force_new = True
        elif arg.startswith("--llm="):
            llm = arg.split("=", 1)[1]
        elif arg.startswith("--user="):
            user_id = arg.split("=", 1)[1]
        elif arg.startswith("--instructions="):
            instructions = arg.split("=", 1)[1]
        elif arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
            if mode not in ["auto", "replay", "resume"]:
                print(f"❌ Invalid mode: {mode}. Use: auto, replay, or resume")
                return
        elif arg.startswith("--max-iterations="):
            try:
                max_iterations = int(arg.split("=", 1)[1])
                if max_iterations < 1:
                    print(f"❌ Invalid max_iterations: {max_iterations}. Must be >= 1")
                    return
            except ValueError:
                print(f"❌ Invalid max_iterations: {arg.split('=', 1)[1]}. Must be a number")
                return
        else:
            print(f"❌ Unknown argument: {arg}")
            return

    # Create agent
    agent = Agent(
        llm=llm,
        tools=TOOLS if use_tools else None,
        instructions=instructions,
        mode=mode,
        max_iterations=max_iterations,
        profile=profile,
        sandbox=sandbox,
    )

    # Continuation logic
    if force_new:
        import uuid

        conversation_id = str(uuid.uuid4())
        context_type = "fresh"
    else:
        conversation_id = get_last_conversation_id(user_id)
        context_type = "continue"

    # Show clean execution header
    config_parts = [llm, mode]
    if not use_tools:
        config_parts.append("no tools")
    if not profile:
        config_parts.append("no profile")
    if instructions:
        config_parts.append("custom instructions")

    print(f"🤖 Cogency Agent ({', '.join(config_parts)}, max_iterations={max_iterations})")
    print(f"👤 User: {user_id}")
    print(f"🔄 Context: {context_type}")
    print(f"❓ Question: {question}")
    print("─" * 50)
    print(f"🆔 Session: {conversation_id[:8]}...")

    # Debug mode - show assembled context
    if debug:
        from ..context import context
        from ..lib.logger import logger

        print("🔍 DEBUG MODE: Assembled Context")
        print("=" * 60)

        messages = context.assemble(question, user_id, conversation_id, agent.tools, agent)
        for msg in messages:
            print(f"[{msg['role'].upper()}] {msg['content']}")

        print("=" * 60)

    try:
        # Streaming execution
        from .display import Renderer

        renderer = Renderer(show_stream=show_stream)
        agent_stream = agent.stream(question, user_id=user_id, conversation_id=conversation_id)
        await renderer.render_stream(agent_stream, show_metrics=True)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
