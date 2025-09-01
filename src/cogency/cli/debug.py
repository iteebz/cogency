"""Core debugging - what agent did vs what should have happened."""

import json
import sqlite3
import sys
import time

from ..core.protocols import Event
from ..lib.storage import get_db_path


def show_conversation(conversation_id: str = None):
    """Show last conversation flow."""
    db_path = get_db_path()

    if not db_path.exists():
        print("❌ No conversations found")
        return

    with sqlite3.connect(db_path) as db:
        if not conversation_id:
            # Get last conversation
            result = db.execute(
                "SELECT conversation_id FROM conversations ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            if not result:
                print("❌ No conversations found")
                return
            conversation_id = result[0]

        # Get full conversation
        messages = db.execute(
            "SELECT type, content, timestamp FROM conversations WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()

        if not messages:
            print(f"❌ No messages found for {conversation_id}")
            return

        print(f"🔍 LAST: {conversation_id}")
        print("=" * 60)

        for msg_type, content, timestamp in messages:
            age = int(time.time() - timestamp)

            if msg_type == Event.USER:
                print(f"\n👤 USER ({age}s ago):")
                print(f"  {content}")

            elif msg_type == Event.THINK:
                print("\n🧠 THINK:")
                first_line = content.split("\n")[0][:80]
                print(f"  {first_line}...")

            elif msg_type == Event.CALLS:
                print("\n🛠️  TOOLS:")
                try:
                    tools = json.loads(content)
                    for i, tool in enumerate(tools):
                        name = tool.get("name", "unknown")
                        args = tool.get("args", {})
                        print(
                            f"  {i+1}. {name}({', '.join(f'{k}={repr(v)}' for k, v in args.items())})"
                        )
                except json.JSONDecodeError:
                    print(f"  ❌ Invalid JSON: {content[:100]}...")

            elif msg_type == Event.RESPOND:
                print("\n🤖 ASSISTANT:")
                print(f"  {content}")

        print("\n" + "=" * 60)
        tool_count = len([m for m in messages if m[0] == Event.CALLS])
        print(f"📊 SUMMARY: {len(messages)} messages, {tool_count} tool executions")


def show_context(conversation_id: str = None):
    """Show exact LLM prompt sent."""
    from ..context.assembly import context
    from ..tools import TOOLS

    db_path = get_db_path()

    if not db_path.exists():
        print("❌ No conversations found")
        return

    with sqlite3.connect(db_path) as db:
        if not conversation_id:
            result = db.execute(
                "SELECT conversation_id FROM conversations ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            if not result:
                print("❌ No conversations found")
                return
            conversation_id = result[0]

        # Handle partial conversation ID matching
        if len(conversation_id) < 36:
            result = db.execute(
                "SELECT conversation_id FROM conversations WHERE conversation_id LIKE ? LIMIT 1",
                (f"{conversation_id}%",),
            ).fetchone()
            if result:
                conversation_id = result[0]
            else:
                print(f"❌ No conversation found matching '{conversation_id}'")
                return

        # Get the user query
        user_msg = db.execute(
            "SELECT content FROM conversations WHERE conversation_id = ? AND type = 'user' ORDER BY timestamp DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()

        if not user_msg:
            print("❌ No user message found")
            return

        query = user_msg[0]
        print(f"🔍 PROMPT: {conversation_id}")
        print("=" * 80)
        print(f"📝 Query: {query}")
        print()

        # Assemble context exactly like the agent does
        messages = context.assemble(query, "ask_user", conversation_id, TOOLS)

        for i, msg in enumerate(messages):
            print(f"🔸 MESSAGE {i+1} [{msg['role'].upper()}]")
            print("-" * 40)
            content = msg["content"]

            # Truncate very long content
            if len(content) > 2000:
                lines = content.split("\n")
                print("\n".join(lines[:30]))
                print(f"\n... [TRUNCATED - {len(lines)-30} more lines] ...\n")
                print("\n".join(lines[-10:]))
            else:
                print(content)
            print()


def query_main():
    """Interactive database query for real debugging."""
    db_path = get_db_path()

    if not db_path.exists():
        print("❌ No database found")
        return

    if not sys.stdin.isatty():
        print("🔍 Database Query (Non-interactive)")
        print("💡 Run in interactive terminal for full interface")
        return

    print("🔍 Database Query Interface")
    print("📊 Commands: conversations, messages <id>, sql <query>, exit")
    print()

    with sqlite3.connect(db_path) as db:
        while True:
            try:
                cmd = input("db> ").strip()
                if not cmd:
                    continue

                if cmd == "exit":
                    break

                if cmd.startswith("conversations"):
                    result = db.execute("""
                        SELECT conversation_id, COUNT(*) as msgs, MAX(timestamp) as last_msg
                        FROM conversations
                        GROUP BY conversation_id
                        ORDER BY last_msg DESC
                        LIMIT 10
                    """).fetchall()

                    print("📋 Recent conversations:")
                    for conv_id, msg_count, last_msg in result:
                        ago = int(time.time() - last_msg)
                        time_ago = f"{ago//60}m ago" if ago > 60 else f"{ago}s ago"
                        print(f"  {conv_id[:8]}... | {msg_count:2d} msgs | {time_ago}")

                elif cmd.startswith("messages "):
                    conv_id = cmd.split(" ", 1)[1].strip()
                    if len(conv_id) < 36:
                        # Partial match
                        result = db.execute(
                            "SELECT conversation_id FROM conversations WHERE conversation_id LIKE ? LIMIT 1",
                            (f"{conv_id}%",),
                        ).fetchone()
                        if result:
                            conv_id = result[0]

                    messages = db.execute(
                        "SELECT type, content FROM conversations WHERE conversation_id = ? ORDER BY timestamp",
                        (conv_id,),
                    ).fetchall()

                    print(f"💬 Messages in {conv_id[:8]}...:")
                    for msg_type, content in messages:
                        preview = (
                            content.replace("\n", "\\n")[:60] + "..."
                            if len(content) > 60
                            else content
                        )
                        print(f"  {msg_type:8s} | {preview}")

                elif cmd.startswith("sql "):
                    query = cmd[4:].strip()
                    try:
                        cursor = db.execute(query)
                        if query.strip().upper().startswith("SELECT"):
                            results = cursor.fetchall()
                            print(f"📊 {len(results)} results")
                            for row in results[:10]:  # Limit output
                                print(f"  {row}")
                        else:
                            print(f"✅ Query executed. Rows affected: {cursor.rowcount}")
                    except Exception as e:
                        print(f"❌ SQL Error: {e}")

                else:
                    print("Commands: conversations, messages <id>, sql <query>, exit")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
