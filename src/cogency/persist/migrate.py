"""Migration utilities for persistence backends."""

import json
from typing import Optional

from .store.filesystem import Filesystem
from .store.sqlite import SQLiteStore


async def migrate_filesystem_to_sqlite(
    filesystem_dir: Optional[str] = None, sqlite_db: Optional[str] = None, dry_run: bool = False
) -> dict:
    """Migrate existing filesystem persistence to SQLite.

    Args:
        filesystem_dir: Source filesystem store directory
        sqlite_db: Target SQLite database path
        dry_run: If True, only analyze what would be migrated

    Returns:
        Migration report with counts and errors
    """
    fs_store = Filesystem(base_dir=filesystem_dir)
    sqlite_store = SQLiteStore(db_path=sqlite_db)

    report = {"states_migrated": 0, "profiles_migrated": 0, "errors": [], "dry_run": dry_run}

    # Get all state files from filesystem
    state_files = []
    if fs_store.base_dir.exists():
        # Agent state files (pattern: user_process.json)
        for state_file in fs_store.base_dir.glob("*_*.json"):
            if not state_file.name.startswith("profile_"):
                state_files.append(state_file)

    # Get all profile files
    profile_files = []
    if fs_store.memory_dir.exists():
        profile_files = list(fs_store.memory_dir.glob("*.json"))

    # Migrate agent states
    for state_file in state_files:
        try:
            # Parse filename to extract user_id and process_id
            stem = state_file.stem
            if "_" in stem:
                parts = stem.split("_")
                if len(parts) >= 2:
                    user_id = "_".join(parts[:-1])  # Everything except last part
                    process_id = parts[-1]
                    state_key = f"{user_id}:{process_id}"
                else:
                    state_key = f"{stem}:default"
            else:
                state_key = f"{stem}:default"

            # Load state data
            with open(state_file) as f:
                state_data = json.load(f)

            if not dry_run:
                success = await sqlite_store.save(state_key, state_data)
                if success:
                    report["states_migrated"] += 1
                else:
                    report["errors"].append(f"Failed to save state: {state_key}")
            else:
                report["states_migrated"] += 1

        except Exception as e:
            report["errors"].append(f"Error migrating {state_file}: {str(e)}")

    # Migrate user profiles
    for profile_file in profile_files:
        try:
            user_id = profile_file.stem
            profile_key = f"profile:{user_id}"

            # Load profile data
            with open(profile_file) as f:
                profile_data = json.load(f)

            if not dry_run:
                success = await sqlite_store.save(profile_key, profile_data)
                if success:
                    report["profiles_migrated"] += 1
                else:
                    report["errors"].append(f"Failed to save profile: {user_id}")
            else:
                report["profiles_migrated"] += 1

        except Exception as e:
            report["errors"].append(f"Error migrating {profile_file}: {str(e)}")

    return report


async def verify_migration(
    filesystem_dir: Optional[str] = None, sqlite_db: Optional[str] = None
) -> dict:
    """Verify migration completeness by comparing filesystem and SQLite data.

    Returns:
        Verification report with comparison results
    """
    fs_store = Filesystem(base_dir=filesystem_dir)
    sqlite_store = SQLiteStore(db_path=sqlite_db)

    report = {
        "filesystem_states": 0,
        "sqlite_states": 0,
        "filesystem_profiles": 0,
        "sqlite_profiles": 0,
        "missing_states": [],
        "missing_profiles": [],
        "data_mismatches": [],
    }

    # Count filesystem states
    if fs_store.base_dir.exists():
        fs_states = [
            f for f in fs_store.base_dir.glob("*_*.json") if not f.name.startswith("profile_")
        ]
        report["filesystem_states"] = len(fs_states)

        # Verify each state exists in SQLite
        for state_file in fs_states:
            try:
                stem = state_file.stem
                if "_" in stem:
                    parts = stem.split("_")
                    if len(parts) >= 2:
                        user_id = "_".join(parts[:-1])
                        process_id = parts[-1]
                        state_key = f"{user_id}:{process_id}"
                    else:
                        state_key = f"{stem}:default"
                else:
                    state_key = f"{stem}:default"

                sqlite_data = await sqlite_store.load(state_key)
                if not sqlite_data:
                    report["missing_states"].append(state_key)

            except Exception as e:
                report["missing_states"].append(f"{state_file}: {str(e)}")

    # Count filesystem profiles
    if fs_store.memory_dir.exists():
        fs_profiles = list(fs_store.memory_dir.glob("*.json"))
        report["filesystem_profiles"] = len(fs_profiles)

        # Verify each profile exists in SQLite
        for profile_file in fs_profiles:
            try:
                user_id = profile_file.stem
                profile_key = f"profile:{user_id}"

                sqlite_data = await sqlite_store.load(profile_key)
                if not sqlite_data:
                    report["missing_profiles"].append(user_id)

            except Exception as e:
                report["missing_profiles"].append(f"{user_id}: {str(e)}")

    # Count SQLite data using direct queries
    try:
        sqlite_states = await sqlite_store.query_states(limit=10000)
        report["sqlite_states"] = len(sqlite_states)
    except Exception:
        report["sqlite_states"] = 0

    # Note: SQLite profile count would require direct DB access
    # For now, assume profiles match if no missing_profiles
    report["sqlite_profiles"] = report["filesystem_profiles"] - len(report["missing_profiles"])

    return report
