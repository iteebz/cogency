"""Advanced knowledge management commands - TIER 2 power user utilities."""

import json
from datetime import datetime, timedelta
from typing import Optional

from cogency.storage.sqlite import SQLite


async def knowledge_command(action: str, query: Optional[str] = None, **kwargs):
    """Handle knowledge management commands."""
    print("🧠 Cogency Knowledge Management")
    print("=" * 50)

    if action == "search":
        if not query:
            print("❌ Error: Search query required")
            print("Usage: cogency knowledge search 'topic'")
            return
        await search_knowledge(query)
    elif action == "stats":
        await knowledge_stats()
    elif action == "export":
        format_type = kwargs.get("format", "json")
        await export_knowledge(format_type)
    elif action == "prune":
        days = kwargs.get("days", 30)
        await prune_knowledge(days)
    else:
        print(f"❌ Unknown knowledge action: {action}")
        print("Available actions: search, stats, export, prune")


async def search_knowledge(query: str, user_id: str = "default", top_k: int = 10):
    """Search knowledge base with relevance scoring."""
    store = SQLite()

    print(f"🔍 Searching knowledge base: '{query}'")
    print("-" * 60)

    try:
        # Use existing knowledge search functionality
        artifacts = await store.search_knowledge(query, user_id, top_k, threshold=0.5)

        if not artifacts:
            print("📭 No knowledge found matching your query")
            print("\nTips:")
            print("- Try broader search terms")
            print("- Use 'cogency knowledge stats' to see available topics")
            return

        print(f"📋 Found {len(artifacts)} relevant knowledge artifacts")
        print()

        for i, artifact in enumerate(artifacts, 1):
            # Calculate relative time
            age = datetime.now() - artifact.created_at
            if age.days > 0:
                age_str = f"{age.days}d ago"
            elif age.seconds > 3600:
                age_str = f"{age.seconds // 3600}h ago"
            else:
                age_str = f"{age.seconds // 60}m ago"

            # Format confidence as percentage
            confidence_pct = int(artifact.confidence * 100)

            print(f"{i:2}. 📌 {artifact.topic}")
            print(f"    📈 Confidence: {confidence_pct}% | 📅 {age_str}")
            print(f"    💬 Context: {artifact.context[:100]}...")

            # Show content preview
            content_preview = artifact.content[:200]
            if len(artifact.content) > 200:
                content_preview += "..."
            print(f"    📝 {content_preview}")

            # Show source conversations if available
            if artifact.source_conversations:
                conv_count = len(artifact.source_conversations)
                print(f"    🔗 From {conv_count} conversation{'s' if conv_count > 1 else ''}")

            print()

    except Exception as e:
        print(f"❌ Knowledge search failed: {str(e)}")


async def knowledge_stats(user_id: str = "default"):
    """Display knowledge base statistics and health."""
    store = SQLite()

    try:
        # Get all knowledge for user (using broad search)
        artifacts = await store.search_knowledge("", user_id, top_k=1000, threshold=0.0)

        if not artifacts:
            print("📭 No knowledge artifacts found")
            print("Knowledge is created automatically during conversations with memory enabled")
            return

        # Calculate statistics
        total_artifacts = len(artifacts)
        topics = {artifact.topic for artifact in artifacts}

        # Confidence distribution
        high_confidence = len([a for a in artifacts if a.confidence >= 0.8])
        medium_confidence = len([a for a in artifacts if 0.5 <= a.confidence < 0.8])
        low_confidence = len([a for a in artifacts if a.confidence < 0.5])

        # Age distribution
        now = datetime.now()
        recent = len([a for a in artifacts if (now - a.created_at).days <= 7])
        this_month = len([a for a in artifacts if (now - a.created_at).days <= 30])
        older = total_artifacts - this_month

        # Most common topics
        topic_counts = {}
        for artifact in artifacts:
            topic_counts[artifact.topic] = topic_counts.get(artifact.topic, 0) + 1

        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        print("📊 Knowledge Base Statistics")
        print("-" * 40)
        print(f"Total artifacts: {total_artifacts}")
        print(f"Unique topics: {len(topics)}")
        print()

        print("📈 Confidence Distribution:")
        print(f"  High (80%+):   {high_confidence:3} artifacts")
        print(f"  Medium (50%+): {medium_confidence:3} artifacts")
        print(f"  Low (<50%):    {low_confidence:3} artifacts")
        print()

        print("📅 Age Distribution:")
        print(f"  Recent (7d):   {recent:3} artifacts")
        print(f"  This month:    {this_month:3} artifacts")
        print(f"  Older:         {older:3} artifacts")
        print()

        if top_topics:
            print("🏷️  Most Common Topics:")
            for topic, count in top_topics[:5]:
                print(f"  {topic[:40]:<40} {count:3} artifacts")

            if len(top_topics) > 5:
                remaining = sum(count for _, count in top_topics[5:])
                print(f"  {'... and others':<40} {remaining:3} artifacts")

    except Exception as e:
        print(f"❌ Knowledge stats failed: {str(e)}")


async def export_knowledge(format_type: str = "json", user_id: str = "default"):
    """Export knowledge base to specified format."""
    store = SQLite()

    if format_type not in ["json", "markdown"]:
        print(f"❌ Unsupported format: {format_type}")
        print("Available formats: json, markdown")
        return

    print(f"📤 Exporting knowledge base as {format_type.upper()}")
    print("-" * 50)

    try:
        # Get all knowledge for user
        artifacts = await store.search_knowledge("", user_id, top_k=1000, threshold=0.0)

        if not artifacts:
            print("📭 No knowledge to export")
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cogency_knowledge_{timestamp}.{format_type}"

        if format_type == "json":
            # Export as structured JSON
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "user_id": user_id,
                "total_artifacts": len(artifacts),
                "artifacts": [],
            }

            for artifact in artifacts:
                export_data["artifacts"].append(
                    {
                        "topic": artifact.topic,
                        "content": artifact.content,
                        "confidence": artifact.confidence,
                        "context": artifact.context,
                        "created_at": artifact.created_at.isoformat(),
                        "updated_at": artifact.updated_at.isoformat(),
                        "source_conversations": artifact.source_conversations,
                        "metadata": artifact.metadata,
                    }
                )

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        else:  # markdown
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# Cogency Knowledge Base Export\n\n")
                f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**User ID:** {user_id}\n")
                f.write(f"**Total Artifacts:** {len(artifacts)}\n\n")
                f.write("---\n\n")

                # Sort by topic for better organization
                artifacts_by_topic = sorted(artifacts, key=lambda x: x.topic)

                for artifact in artifacts_by_topic:
                    f.write(f"## {artifact.topic}\n\n")
                    f.write(f"**Confidence:** {int(artifact.confidence * 100)}%\n")
                    f.write(f"**Created:** {artifact.created_at.strftime('%Y-%m-%d')}\n")
                    if artifact.context:
                        f.write(f"**Context:** {artifact.context}\n")
                    f.write("\n")
                    f.write(f"{artifact.content}\n\n")

                    if artifact.source_conversations:
                        f.write(f"*Source: {len(artifact.source_conversations)} conversation(s)*\n")

                    f.write("---\n\n")

        print("✅ Knowledge exported successfully")
        print(f"📁 File: {filename}")
        print(f"📊 Exported {len(artifacts)} artifacts")

    except Exception as e:
        print(f"❌ Knowledge export failed: {str(e)}")


async def prune_knowledge(days: int = 30, user_id: str = "default"):
    """Clean old/irrelevant knowledge based on age and confidence."""
    store = SQLite()

    print(f"🧹 Pruning knowledge older than {days} days")
    print("-" * 50)

    try:
        # Get all knowledge for analysis
        artifacts = await store.search_knowledge("", user_id, top_k=1000, threshold=0.0)

        if not artifacts:
            print("📭 No knowledge to prune")
            return

        # Determine pruning criteria
        cutoff_date = datetime.now() - timedelta(days=days)

        # Candidates for pruning: old AND low confidence
        prune_candidates = []
        for artifact in artifacts:
            # Prune if old and low confidence
            if artifact.created_at < cutoff_date and artifact.confidence < 0.6:
                prune_candidates.append(artifact)

        if not prune_candidates:
            print("✨ No knowledge needs pruning")
            print(f"All {len(artifacts)} artifacts are recent or high-confidence")
            return

        print(f"🎯 Found {len(prune_candidates)} artifacts to prune:")
        print()

        for i, artifact in enumerate(prune_candidates[:10], 1):
            age = datetime.now() - artifact.created_at
            confidence_pct = int(artifact.confidence * 100)
            print(f"{i:2}. {artifact.topic[:50]:<50} {age.days}d old, {confidence_pct}% confidence")

        if len(prune_candidates) > 10:
            print(f"    ... and {len(prune_candidates) - 10} more")

        print()
        response = input("❓ Proceed with pruning? (y/N): ").strip().lower()

        if response != "y":
            print("❌ Pruning cancelled")
            return

        # Perform pruning (would need to implement delete_knowledge by artifact)
        # For now, show what would be pruned
        pruned_count = 0
        for _artifact in prune_candidates:
            # TODO: Implement artifact deletion in storage layer
            # success = await store.delete_knowledge(artifact.topic, user_id)
            # if success:
            #     pruned_count += 1
            pruned_count += 1  # Simulated for now

        print(f"✅ Pruned {pruned_count} knowledge artifacts")
        print(f"📊 Remaining: {len(artifacts) - pruned_count} artifacts")

        # TODO: Remove this note when deletion is implemented
        print("\n⚠️  Note: Actual deletion not yet implemented - this was a preview")

    except Exception as e:
        print(f"❌ Knowledge pruning failed: {str(e)}")
