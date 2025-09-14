#!/usr/bin/env python3
"""Cogency CLI - agent execution."""

import asyncio
import sqlite3
import warnings

from .. import Agent
from ..lib.storage import Paths
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
    db_path = Paths.db()

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


async def run_agent(
    question: str,
    llm: str = "gemini",
    mode: str = "auto",
    user: str = "ask_user",
    instructions: str = None,
    max_iterations: int = 10,
    no_tools: bool = False,
    no_profile: bool = False,
    no_sandbox: bool = False,
    new: bool = False,
    debug: bool = False,
    verbose: bool = False,
):
    """Run agent with given parameters."""

    if debug:
        from ..lib.logger import set_debug

        set_debug(True)

    # Create agent
    agent = Agent(
        llm=llm,
        tools=TOOLS if not no_tools else None,
        instructions=instructions,
        mode=mode,
        max_iterations=max_iterations,
        profile=not no_profile,
        sandbox=not no_sandbox,
    )

    # Continuation logic
    if new:
        import uuid

        conversation_id = str(uuid.uuid4())
        context_type = "fresh"
    else:
        conversation_id = get_last_conversation_id(user)
        context_type = "continue"

    # Show clean execution header
    config_parts = [llm, mode]
    if no_tools:
        config_parts.append("no tools")
    if no_profile:
        config_parts.append("no profile")
    if instructions:
        config_parts.append("custom instructions")

    # Show minimal header only with --verbose
    if verbose:
        print(f"Cogency Agent ({', '.join(config_parts)}, max_iterations={max_iterations})")
        print(f"User: {user}")
        print(f"Context: {context_type}")
        session_name = f"session_{len(conversation_id) % 100:02d}"
        print(f"Session: {session_name}")
        print("─" * 50)

    # Debug mode - show assembled context
    if debug:
        from ..context import context

        print("DEBUG MODE: Assembled Context")
        print("=" * 60)
        messages = await context.assemble(question, user, conversation_id, agent.config)
        for msg in messages:
            print(f"[{msg['role'].upper()}] {msg['content']}")
        print("=" * 60)

    try:
        # Streaming execution with observation
        from ..lib.observer import observe
        from .display import Renderer

        @observe(agent)
        async def observed_stream():
            try:
                async for event in agent(
                    question, user_id=user, conversation_id=conversation_id, chunks=False
                ):
                    yield event
            except asyncio.CancelledError:
                # Agent stream was cancelled - yield cancellation event and re-raise
                yield {
                    "type": "cancelled",
                    "content": "Task interrupted by user",
                    "timestamp": __import__("time").time(),
                }
                raise  # Re-raise for proper cleanup

        # Create single stream instance
        stream_instance = observed_stream()

        renderer = Renderer(verbose=verbose)
        await renderer.render_stream(stream_instance)

        # Always show metrics after stream completion
        if hasattr(observed_stream, "metrics"):
            metrics = observed_stream.metrics
            renderer.show_metrics(metrics)

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Legacy main function for backwards compatibility."""
    from . import main as cli_main

    cli_main()


if __name__ == "__main__":
    asyncio.run(main())
