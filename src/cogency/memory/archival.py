"""Archival memory system with write-time intelligence."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from resilient_result import Err, Ok, Result

from cogency.events import emit


class TopicArtifact:
    """Topic artifact with metadata and content."""

    def __init__(self, topic: str, content: str, metadata: Optional[Dict] = None):
        self.topic = topic
        self.content = content
        self.metadata = metadata or {}
        self.created = self.metadata.get("created", datetime.now().isoformat())
        self.updated = self.metadata.get("updated", datetime.now().isoformat())
        self.source_conversations = self.metadata.get("source_conversations", [])

    @classmethod
    def from_markdown(cls, topic: str, markdown_content: str) -> "TopicArtifact":
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
                return cls(topic, content.strip(), metadata)

        # No frontmatter, just content
        return cls(topic, markdown_content.strip())

    def to_markdown(self) -> str:
        """Convert to markdown with YAML frontmatter."""
        metadata = {
            "topic": self.topic,
            "created": self.created,
            "updated": self.updated,
            "source_conversations": self.source_conversations,
        }

        frontmatter = yaml.dump(metadata, default_flow_style=False)
        return f"---\n{frontmatter}---\n\n{self.content}"


class ArchivalMemory:
    """Archival memory system with write-time intelligence.

    Handles topic artifact storage with:
    - Write-time LLM-based merging
    - Semantic search via vector embeddings
    - Hierarchical markdown organization
    """

    def __init__(self, llm_provider, embed_provider, base_path: str = None):
        self.llm = llm_provider
        self.embed = embed_provider

        if base_path is None:
            from cogency.config.dataclasses import PathsConfig

            paths = PathsConfig()
            base_path = os.path.expanduser(paths.memory)

        self.base_path = Path(base_path)
        self._topic_cache = {}  # Cache for loaded topics
        self._embedding_cache = {}  # Cache for topic embeddings

    def _get_user_path(self, user_id: str) -> Path:
        """Get memory path for specific user."""
        return self.base_path / user_id / "topics"

    def _get_topic_path(self, user_id: str, topic: str) -> Path:
        """Get file path for topic artifact."""
        user_path = self._get_user_path(user_id)
        # Sanitize topic name for filesystem
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_topic = safe_topic.replace(" ", "-").lower()
        return user_path / f"{safe_topic}.md"

    async def store_knowledge(
        self, user_id: str, topic: str, content: str, conversation_id: str = None
    ) -> Result:
        """Store new knowledge as topic document (merging handled by archive step).

        Args:
            user_id: User identifier
            topic: Topic name for categorization
            content: Knowledge content to store
            conversation_id: Optional conversation reference

        Returns:
            Result indicating success/failure
        """
        emit("memory", operation="store", user_id=user_id, topic=topic, status="start")

        try:
            # Create new topic artifact (no automatic merging)
            artifact = TopicArtifact(topic, content)

            # Add conversation reference if provided
            if conversation_id and conversation_id not in artifact.source_conversations:
                artifact.source_conversations.append(conversation_id)

            # Update timestamp
            artifact.updated = datetime.now().isoformat()

            # Save to filesystem
            await self._save_topic(user_id, artifact)

            # Update embeddings for search
            await self._update_embeddings(user_id, artifact)

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

    async def _load_topic(self, user_id: str, topic: str) -> Optional[TopicArtifact]:
        """Load existing topic artifact."""
        topic_path = self._get_topic_path(user_id, topic)

        if not topic_path.exists():
            return None

        try:
            content = topic_path.read_text(encoding="utf-8")
            return TopicArtifact.from_markdown(topic, content)
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

    async def _save_merged_topic(
        self, user_id: str, topic: str, merged_content: str
    ) -> TopicArtifact:
        """Save merged topic content (merge logic handled by archive step)."""
        # Create artifact with merged content
        artifact = TopicArtifact(topic, merged_content)
        artifact.updated = datetime.now().isoformat()

        # Save to storage
        await self._save_topic(user_id, artifact)

        return artifact

    async def _save_topic(self, user_id: str, artifact: TopicArtifact) -> None:
        """Save topic artifact to filesystem."""
        topic_path = self._get_topic_path(user_id, artifact.topic)

        # Ensure directory exists
        topic_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown content
        markdown_content = artifact.to_markdown()
        topic_path.write_text(markdown_content, encoding="utf-8")

        # Update cache
        cache_key = f"{user_id}:{artifact.topic}"
        self._topic_cache[cache_key] = artifact

    async def _update_embeddings(self, user_id: str, artifact: TopicArtifact) -> None:
        """Update vector embeddings for semantic search."""
        try:
            from resilient_result import unwrap

            # Generate embedding for topic content
            embed_result = await self.embed.embed(artifact.content)
            embedding = unwrap(embed_result)

            if isinstance(embedding, list) and embedding:
                # Store embedding (simple in-memory cache for now)
                cache_key = f"{user_id}:{artifact.topic}"
                self._embedding_cache[cache_key] = {
                    "embedding": embedding[0] if isinstance(embedding[0], list) else embedding,
                    "content": artifact.content,
                    "topic": artifact.topic,
                    "updated": artifact.updated,
                }

        except Exception as e:
            emit(
                "memory",
                operation="embed",
                user_id=user_id,
                topic=artifact.topic,
                status="error",
                error=str(e),
            )
            # Non-critical error - continue without embeddings

    async def search_topics(
        self, user_id: str, query: str, limit: int = 3, min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search topics using semantic similarity.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of matching topic results with similarity scores
        """
        emit("memory", operation="search", user_id=user_id, query=query, status="start")

        try:
            # Generate query embedding
            from resilient_result import unwrap

            embed_result = await self.embed.embed(query)
            query_embedding = unwrap(embed_result)

            if isinstance(query_embedding, list) and query_embedding:
                query_vector = (
                    query_embedding[0] if isinstance(query_embedding[0], list) else query_embedding
                )

                # Search cached embeddings
                results = []
                for cache_key, cached_data in self._embedding_cache.items():
                    if not cache_key.startswith(f"{user_id}:"):
                        continue

                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_vector, cached_data["embedding"])

                    if similarity >= min_similarity:
                        results.append(
                            {
                                "topic": cached_data["topic"],
                                "content": cached_data["content"],
                                "similarity": similarity,
                                "updated": cached_data["updated"],
                            }
                        )

                # Sort by similarity and limit results
                results.sort(key=lambda x: x["similarity"], reverse=True)
                results = results[:limit]

                emit(
                    "memory",
                    operation="search",
                    user_id=user_id,
                    query=query,
                    status="complete",
                    results=len(results),
                )

                return results

            return []

        except Exception as e:
            emit(
                "memory",
                operation="search",
                user_id=user_id,
                query=query,
                status="error",
                error=str(e),
            )
            return []

    async def load_user_topics(self, user_id: str) -> List[str]:
        """Load all topic names for a user."""
        user_path = self._get_user_path(user_id)

        if not user_path.exists():
            return []

        topics = []
        for topic_file in user_path.glob("*.md"):
            topic_name = topic_file.stem.replace("-", " ").title()
            topics.append(topic_name)

        return sorted(topics)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def initialize(self, user_id: str) -> None:
        """Initialize memory system for user (load existing topics into cache)."""
        emit("memory", operation="initialize", user_id=user_id, status="start")

        try:
            topics = await self.load_user_topics(user_id)

            # Load existing topics into cache and generate embeddings
            for topic_name in topics:
                artifact = await self._load_topic(user_id, topic_name)
                if artifact:
                    await self._update_embeddings(user_id, artifact)

            emit(
                "memory",
                operation="initialize",
                user_id=user_id,
                status="complete",
                topics_loaded=len(topics),
            )

        except Exception as e:
            emit("memory", operation="initialize", user_id=user_id, status="error", error=str(e))
            raise
