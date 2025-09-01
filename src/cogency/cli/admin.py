"""Admin CLI - database management and cleanup operations."""

import json
import sqlite3
import sys
import time

from ..lib.storage import get_cogency_dir, get_db_path, load_profile


def show_stats():
    """Show database statistics and conversation analytics."""
    db_path = get_db_path()

    if not db_path.exists():
        print("✅ No conversation database found")
        return

    print(f"🗃️ Database: {db_path}")

    with sqlite3.connect(db_path) as db:
        # Total records
        total = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        print(f"📊 Total records: {total}")

        if total == 0:
            return

        # Records by conversation
        conversations = db.execute("""
            SELECT conversation_id, COUNT(*) as records,
                   MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
            FROM conversations
            GROUP BY conversation_id
            ORDER BY records DESC
            LIMIT 10
        """).fetchall()

        print("\n🔍 Top conversations by record count:")
        for conv_id, count, first, _last in conversations:
            age_hours = (time.time() - first) / 3600
            print(f"  {conv_id[:20]:<20} | {count:>4} records | {age_hours:.1f}h old")

        # Records by type
        types = db.execute("""
            SELECT type, COUNT(*) as count
            FROM conversations
            GROUP BY type
            ORDER BY count DESC
        """).fetchall()

        print("\n📝 Records by type:")
        for record_type, count in types:
            print(f"  {record_type:<15} | {count:>4} records")


def show_users():
    """Show all user profiles."""
    db_path = get_db_path()

    if not db_path.exists():
        print("✅ No database found")
        return

    with sqlite3.connect(db_path) as db:
        try:
            profiles = db.execute("""
                SELECT user_id, MAX(version) as latest_version, MAX(created_at) as last_updated, char_count
                FROM profiles
                GROUP BY user_id
                ORDER BY last_updated DESC
            """).fetchall()

            if not profiles:
                print("📝 No user profiles found")
                return

            print(f"🧠 User Profiles ({len(profiles)} users):")
            for user_id, version, updated, chars in profiles:
                age = (time.time() - updated) / 3600  # hours
                print(f"  {user_id:<20} | v{version} | {chars:>3} chars | {age:.1f}h ago")

        except sqlite3.OperationalError:
            print("📝 No profiles table found")


def show_user(user_id: str):
    """Show specific user profile and conversations."""
    db_path = get_db_path()

    if not db_path.exists():
        print("✅ No database found")
        return

    # Show profile
    try:
        profile = load_profile(user_id)
        if profile:
            print(f"🧠 Profile for {user_id}:")
            print(json.dumps(profile, indent=2))
        else:
            print(f"📝 No profile found for {user_id}")
    except Exception as e:
        print(f"❌ Error fetching profile: {e}")

    # Show conversations
    with sqlite3.connect(db_path) as db:
        conversations = db.execute(
            """
            SELECT conversation_id, COUNT(*) as records, MIN(timestamp) as first, MAX(timestamp) as last
            FROM conversations
            WHERE conversation_id LIKE ?
            GROUP BY conversation_id
            ORDER BY last DESC
        """,
            (f"{user_id}%",),
        ).fetchall()

        if conversations:
            print(f"\n💬 Conversations for {user_id}:")
            for conv_id, count, _first, last in conversations:
                age = (time.time() - last) / 3600
                print(f"  {conv_id:<30} | {count:>3} msgs | {age:.1f}h ago")
        else:
            print(f"\n💬 No conversations found for {user_id}")


def nuke_sandbox():
    """Nuclear cleanup of sandbox directory."""
    sandbox_path = get_cogency_dir() / "sandbox"

    if not sandbox_path.exists():
        print("✅ No sandbox directory found")
        return 0

    # Count files before
    file_count = sum(1 for _ in sandbox_path.rglob("*") if _.is_file())
    print(f"🗂️ Sandbox: {sandbox_path} ({file_count} files)")

    if file_count == 0:
        print("✅ Sandbox already empty")
        return 0

    import shutil

    shutil.rmtree(sandbox_path)
    sandbox_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Nuked sandbox - {file_count} files deleted")
    return file_count


def nuke_everything():
    """Nuclear cleanup - delete everything (DB + sandbox)."""
    db_path = get_db_path()

    # Count what we're about to nuke
    db_records = 0
    if db_path.exists():
        with sqlite3.connect(db_path) as db:
            db_records = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            print(f"🗃️ Database: {db_path} ({db_records} records)")
    else:
        print("🗃️ Database: No database found")

    sandbox_files = nuke_sandbox()

    total_items = db_records + sandbox_files
    if total_items == 0:
        print("✅ Nothing to nuke - already clean")
        return

    print(
        f"\n💣 NUCLEAR CLEANUP: {db_records} DB records + {sandbox_files} sandbox files = {total_items} total"
    )
    confirm = input("Type 'yes' to confirm nuclear cleanup: ")

    if confirm.lower() == "yes":
        if db_path.exists():
            db_path.unlink()
            print(f"✅ Nuked database - {db_records} records deleted")
        print(f"✅ NUCLEAR CLEANUP COMPLETE - {total_items} items deleted")
    else:
        print("❌ Nuclear cleanup cancelled")


def users_main():
    """Users CLI main entry."""
    if len(sys.argv) < 3:
        # Show all users by default
        show_users()
        return

    user_id = sys.argv[2]
    if user_id.startswith("--"):
        print(f"❌ Unknown users option: {user_id}")
        return

    # Show specific user
    show_user(user_id)
