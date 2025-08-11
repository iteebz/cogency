"""Archive storage - pure file I/O functions."""

from pathlib import Path
from typing import Optional

import yaml
from resilient_result import Err, Ok, Result

from cogency.config.paths import paths
from cogency.events import emit

from .types import TopicArtifact


def get_user_path(user_id: str, base_path: str = None) -> Path:
    """Get memory path for specific user."""
    if base_path is None:
        base_path = paths.memory
    return Path(base_path) / user_id / "topics"


def get_topic_path(user_id: str, topic: str, base_path: str = None) -> Path:
    """Get file path for topic artifact."""
    user_path = get_user_path(user_id, base_path)
    # Sanitize topic name for filesystem
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_topic = safe_topic.replace(" ", "-").lower()
    return user_path / f"{safe_topic}.md"


def to_markdown(artifact: TopicArtifact) -> str:
    """Convert artifact to markdown with YAML frontmatter."""
    metadata = {
        "topic": artifact.topic,
        "created": artifact.created,
        "updated": artifact.updated,
        "source_conversations": artifact.source_conversations,
    }

    frontmatter = yaml.dump(metadata, default_flow_style=False)
    return f"---\n{frontmatter}---\n\n{artifact.content}"


def from_markdown(topic: str, markdown_content: str) -> TopicArtifact:
    """Parse markdown file with YAML frontmatter."""
    lines = markdown_content.split("\n")

    if lines and lines[0].strip() == "---":
        # Find end of frontmatter
        frontmatter_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                frontmatter_end = i
                break

        if frontmatter_end:
            frontmatter = "\n".join(lines[1:frontmatter_end])
            content = "\n".join(lines[frontmatter_end + 1 :])
            try:
                metadata = yaml.safe_load(frontmatter) or {}
            except yaml.YAMLError:
                metadata = {}
            return TopicArtifact(topic, content.strip(), metadata=metadata)

    # No frontmatter, just content
    return TopicArtifact(topic, markdown_content.strip())


async def load_topic(user_id: str, topic: str, base_path: str = None) -> Optional[TopicArtifact]:
    """Load existing topic artifact."""
    topic_path = get_topic_path(user_id, topic, base_path)

    if not topic_path.exists():
        return None

    try:
        content = topic_path.read_text(encoding="utf-8")
        return from_markdown(topic, content)
    except Exception as e:
        emit(
            "memory",
            operation="load_topic",
            user_id=user_id,
            topic=topic,
            status="error",
            error=str(e),
        )
        return None


async def save_topic(user_id: str, artifact: TopicArtifact, base_path: str = None) -> None:
    """Save topic artifact to filesystem."""
    topic_path = get_topic_path(user_id, artifact.topic, base_path)

    # Ensure directory exists
    topic_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown content
    markdown_content = to_markdown(artifact)
    topic_path.write_text(markdown_content, encoding="utf-8")


async def load_user_topics(user_id: str, base_path: str = None) -> list[str]:
    """Load all topic names for a user."""
    user_path = get_user_path(user_id, base_path)

    if not user_path.exists():
        return []

    topics = []
    for topic_file in user_path.glob("*.md"):
        topic_name = topic_file.stem.replace("-", " ").title()
        topics.append(topic_name)

    return sorted(topics)


async def store_knowledge(
    user_id: str, topic: str, content: str, conversation_id: str = None, base_path: str = None
) -> Result:
    """Store new knowledge as topic document."""
    emit("memory", operation="store", user_id=user_id, topic=topic, status="start")

    try:
        # Create new topic artifact
        artifact = TopicArtifact(topic, content)

        # Add conversation reference if provided
        if conversation_id and conversation_id not in artifact.source_conversations:
            artifact.source_conversations.append(conversation_id)

        # Update timestamp
        from datetime import datetime

        artifact.updated = datetime.now().isoformat()

        # Save to filesystem
        await save_topic(user_id, artifact, base_path)

        emit("memory", operation="store", user_id=user_id, topic=topic, status="complete")
        return Ok({"topic": topic, "updated": True})

    except Exception as e:
        emit(
            "memory",
            operation="store",
            user_id=user_id,
            topic=topic,
            status="error",
            error=str(e),
        )
        return Err(f"Failed to store knowledge: {str(e)}")
