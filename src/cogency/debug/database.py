"""Database-First debugging utilities for dogfooding analysis."""

import json
from pathlib import Path
from typing import Optional

import aiosqlite


class StateAnalyzer:
    """Query state database for execution analysis."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            import os

            from cogency.config.dataclasses import PathsConfig

            paths = PathsConfig()
            base_path = Path(os.path.expanduser(paths.base_dir))
            self.db_path = base_path / "store.db"
        else:
            self.db_path = Path(db_path)

    async def recent_conversations(self, user_id: str = "default", limit: int = 10) -> list[dict]:
        """Get recent conversation history."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT conversation_id, conversation_data, updated_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            results = []
            async for row in cursor:
                conv_data = json.loads(row[1])
                results.append(
                    {
                        "conversation_id": row[0],
                        "message_count": len(conv_data.get("messages", [])),
                        "last_updated": row[2],
                        "conversation_data": conv_data,
                    }
                )
            return results

    async def workspace_analysis(self, user_id: str = "default", limit: int = 5) -> list[dict]:
        """Analyze recent task workspaces."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT task_id, workspace_data, updated_at
                FROM task_workspaces
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            results = []
            async for row in cursor:
                workspace_data = json.loads(row[1])
                results.append(
                    {
                        "task_id": row[0],
                        "objective": workspace_data.get("objective", ""),
                        "insights_count": len(workspace_data.get("insights", [])),
                        "facts_count": len(workspace_data.get("facts", {})),
                        "updated_at": row[2],
                        "workspace_data": workspace_data,
                    }
                )
            return results

    async def user_profile_evolution(self, user_id: str = "default") -> Optional[dict]:
        """Get user profile with evolution tracking."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def format_analysis(
        self, conversations: list[dict], workspaces: list[dict], profile: dict
    ) -> str:
        """Format analysis for readable output."""
        output = []

        output.append("🗄️  DATABASE ANALYSIS")
        output.append("=" * 50)

        if profile:
            output.append("\n👤 USER PROFILE:")
            output.append(f"   Interactions: {profile.get('interaction_count', 0)}")
            output.append(f"   Expertise: {', '.join(profile.get('expertise_areas', []))}")
            output.append(f"   Goals: {len(profile.get('goals', []))} active")

        output.append(f"\n💬 RECENT CONVERSATIONS ({len(conversations)}):")
        for conv in conversations[:3]:
            output.append(
                f"   {conv['conversation_id'][:8]}... | {conv['message_count']} messages | {conv['last_updated']}"
            )

        output.append(f"\n🛠️  RECENT TASKS ({len(workspaces)}):")
        for ws in workspaces[:3]:
            output.append(
                f"   {ws['task_id'][:8]}... | {ws['objective'][:40]}... | {ws['insights_count']} insights | {ws['updated_at']}"
            )

        return "\n".join(output)


async def analyze_state(user_id: str = "default") -> str:
    """Quick state analysis for dogfooding."""
    analyzer = StateAnalyzer()

    conversations = await analyzer.recent_conversations(user_id)
    workspaces = await analyzer.workspace_analysis(user_id)
    profile = await analyzer.user_profile_evolution(user_id)

    return analyzer.format_analysis(conversations, workspaces, profile)
