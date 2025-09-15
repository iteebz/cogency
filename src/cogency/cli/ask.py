#!/usr/bin/env python3
"""Cogency CLI with conversation continuity and cancellation handling."""

import asyncio
import sqlite3
import warnings

from .. import Agent
from ..lib.paths import Paths

warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")


def get_last_conversation_id(user_id: str) -> str:
    """Get the last conversation ID for continuation, or create new one."""
    db_path = Paths.db()

    if not db_path.exists():
        import uuid

        return str(uuid.uuid4())

    try:
        with sqlite3.connect(db_path) as db:
            result = db.execute(
                "SELECT conversation_id FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
                (user_id,),
            ).fetchone()

            if result:
                return result[0]
            import uuid

            return str(uuid.uuid4())

    except Exception:
        import uuid

        return str(uuid.uuid4())


async def run_agent(
    question: str,
    llm: str = "gemini",
    mode: str = "auto",
    new: bool = False,
    debug: bool = False,
):
    """Run agent with given parameters."""

    agent = Agent(
        llm=llm,
        mode=mode,
        debug=debug,
    )

    user = "ask_user"
    if new:
        import uuid

        conversation_id = str(uuid.uuid4())
    else:
        conversation_id = get_last_conversation_id(user)

    try:
        from .display import Renderer

        async def stream_with_cancellation():
            try:
                async for event in agent(
                    question, user_id=user, conversation_id=conversation_id, chunks=False
                ):
                    yield event
            except asyncio.CancelledError:
                yield {
                    "type": "cancelled",
                    "content": "Task interrupted by user",
                    "timestamp": __import__("time").time(),
                }
                raise

        renderer = Renderer()
        await renderer.render_stream(stream_with_cancellation())

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
