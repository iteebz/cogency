"""Core debugging - what agent did vs what should have happened."""

import json
import sqlite3
import time

from ..context.system import prompt
from ..lib.paths import Paths
from ..lib.storage import SQLite
from ..tools import TOOLS


def show_conversation(conversation_id: str = None):
    """Show last conversation flow."""
    SQLite()

    if not conversation_id:
        # Get last conversation ID from database

        db_path = Paths.db()
        if not db_path.exists():
            print("No conversations found")
            return

        with sqlite3.connect(db_path) as db:
            result = db.execute(
                "SELECT conversation_id FROM conversations ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            if not result:
                print("No conversations found")
                return
            conversation_id = result[0]

    # Load messages using storage abstraction
    try:
        messages = []

        with sqlite3.connect(Paths.db()) as db:
            rows = db.execute(
                "SELECT type, content, timestamp FROM conversations WHERE conversation_id = ? ORDER BY timestamp",
                (conversation_id,),
            ).fetchall()
            messages = [(row[0], row[1], row[2]) for row in rows]
    except Exception:
        print(f"No messages found for {conversation_id}")
        return

    if not messages:
        print(f"No messages found for {conversation_id}")
        return

    print(f"LAST: {conversation_id}")

    for msg_type, content, timestamp in messages:
        age = int(time.time() - timestamp)

        if msg_type == "user":
            print(f"\nUSER ({age}s ago): {content}")
        elif msg_type == "think":
            print(f"\nTHINK: {content}")
        elif msg_type == "call":
            print("\nTOOL:")
            try:
                tool = json.loads(content)
                name = tool.get("name", "unknown")
                args = tool.get("args", {})
                print(f"  {name}({', '.join(f'{k}={repr(v)}' for k, v in args.items())})")
            except json.JSONDecodeError:
                print(f"  Invalid JSON: {content}")
        elif msg_type == "respond":
            print(f"\nASSISTANT: {content}")

    tool_count = len([m for m in messages if m[0] == "call"])
    print(f"SUMMARY: {len(messages)} messages, {tool_count} tool executions")


def show_system_prompt():
    """Show current system prompt configuration."""

    print("CURRENT SYSTEM PROMPT")
    print("=" * 50)

    system_prompt = prompt(tools=TOOLS, include_security=True)
    print(system_prompt)
    print("\n" + "=" * 50)
    print(f"Total length: {len(system_prompt)} characters")


def show_context(conversation_id: str = None):
    """Show exact LLM prompt sent."""
    storage = SQLite()

    if not conversation_id:
        # Get last conversation ID

        db_path = Paths.db()
        if not db_path.exists():
            print("No conversations found")
            return

        with sqlite3.connect(db_path) as db:
            result = db.execute(
                "SELECT conversation_id FROM conversations ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            if not result:
                print("No conversations found")
                return
            conversation_id = result[0]

    # Handle partial conversation ID matching
    if len(conversation_id) < 36:
        with sqlite3.connect(Paths.db()) as db:
            result = db.execute(
                "SELECT conversation_id FROM conversations WHERE conversation_id LIKE ? LIMIT 1",
                (f"{conversation_id}%",),
            ).fetchone()
            if result:
                conversation_id = result[0]
            else:
                print(f"No conversation found matching '{conversation_id}'")
                return

    # Get the user query

    with sqlite3.connect(Paths.db()) as db:
        user_msg = db.execute(
            "SELECT content FROM conversations WHERE conversation_id = ? AND type = 'user' ORDER BY timestamp DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()

    if not user_msg:
        print("No user message found")
        return

    query = user_msg[0]
    print(f"CONTEXT: {conversation_id}")
    print(f"Query: {query}")

    try:
        import asyncio

        from ..context import assemble
        from ..tools import TOOLS

        messages = asyncio.run(
            assemble(
                query,
                "ask_user",
                conversation_id,
                tools=TOOLS,
                storage=storage,
                history_window=20,
                profile_enabled=True,
            )
        )

        for i, msg in enumerate(messages):
            print(f"\nMESSAGE {i + 1} [{msg['role'].upper()}]")
            content = msg["content"]
            print(content)

    except Exception as e:
        print(f"Failed to assemble context: {e}")
