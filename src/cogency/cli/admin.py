"""Admin CLI - database statistics."""

import json
import sqlite3
import time

from ..lib.paths import Paths


def show_stats():
    """Show database statistics."""
    db_path = Paths.db()

    if not db_path.exists():
        print("No database found")
        return

    with sqlite3.connect(db_path) as db:
        total = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        print(f"Total records: {total}")

        if total == 0:
            return

        conversations = db.execute("""
            SELECT conversation_id, COUNT(*) as records, MIN(timestamp) as first_seen
            FROM conversations GROUP BY conversation_id ORDER BY records DESC LIMIT 5
        """).fetchall()

        print("\nTop conversations:")
        for conv_id, count, first in conversations:
            age_hours = (time.time() - first) / 3600
            print(f"  {conv_id[:20]} | {count} records | {age_hours:.1f}h old")

        types = db.execute("""
            SELECT type, COUNT(*) as count FROM conversations GROUP BY type ORDER BY count DESC
        """).fetchall()

        print("\nBy type:")
        for record_type, count in types:
            print(f"  {record_type}: {count}")


def show_users():
    """Show user profiles."""
    db_path = Paths.db()

    if not db_path.exists():
        print("No database found")
        return

    with sqlite3.connect(db_path) as db:
        try:
            profiles = db.execute("""
                SELECT user_id, MAX(version) as version, MAX(created_at) as updated, char_count
                FROM profiles GROUP BY user_id ORDER BY updated DESC
            """).fetchall()

            if not profiles:
                print("No profiles found")
                return

            print(f"Profiles ({len(profiles)} users):")
            for user_id, version, updated, chars in profiles:
                age = (time.time() - updated) / 3600
                print(f"  {user_id} | v{version} | {chars} chars | {age:.1f}h ago")

        except sqlite3.OperationalError:
            print("No profiles table")


def show_user(user_id: str):
    """Show specific user profile."""
    import asyncio

    from ..context.profile import get

    try:
        profile = asyncio.run(get(user_id))
        if profile:
            print(json.dumps(profile, indent=2))
        else:
            print("No profile found")
    except Exception as e:
        print(f"Error: {e}")
