"""Unit tests for ArchivalMemory system."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from resilient_result import Err, Ok

from cogency.memory.archival import ArchivalMemory, TopicArtifact


class TestTopicArtifact:
    def test_create_basic_artifact(self):
        artifact = TopicArtifact("Python", "List comprehensions are fast")
        assert artifact.topic == "Python"
        assert artifact.content == "List comprehensions are fast"
        assert artifact.source_conversations == []

    def test_from_markdown_with_frontmatter(self):
        markdown = """---
topic: Python
created: 2024-01-01T00:00:00
source_conversations: [conv1, conv2]
---

# Python Performance

List comprehensions are faster than for loops."""

        artifact = TopicArtifact.from_markdown("Python", markdown)
        assert artifact.topic == "Python"
        assert "# Python Performance" in artifact.content
        assert artifact.metadata["source_conversations"] == ["conv1", "conv2"]

    def test_to_markdown_format(self):
        artifact = TopicArtifact("Python", "Fast code", {"created": "2024-01-01"})
        markdown = artifact.to_markdown()

        assert "---" in markdown
        assert "topic: Python" in markdown
        assert "Fast code" in markdown


class TestArchivalMemory:
    @pytest.fixture
    def mock_llm(self):
        llm = AsyncMock()
        llm.generate.return_value = Ok("Merged content")
        return llm

    @pytest.fixture
    def mock_embed(self):
        embed = AsyncMock()
        embed.embed.return_value = Ok([[0.1, 0.2, 0.3]])
        return embed

    @pytest.fixture
    def archival_memory(self, mock_llm, mock_embed):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = ArchivalMemory(mock_llm, mock_embed, str(Path(temp_dir) / "memory"))
            yield memory

    def test_user_path_generation(self, archival_memory):
        path = archival_memory._get_user_path("user123")
        assert "user123/topics" in str(path)

    def test_topic_path_sanitization(self, archival_memory):
        path = archival_memory._get_topic_path("user1", "Python Performance & Tips")
        assert path.name == "python-performance--tips.md"

    @pytest.mark.asyncio
    async def test_store_new_knowledge(self, archival_memory):
        result = await archival_memory.store_knowledge(
            "user1", "Python", "List comprehensions are fast"
        )

        assert result.success
        assert result.data["topic"] == "Python"

    @pytest.mark.asyncio
    async def test_search_with_no_results(self, archival_memory):
        results = await archival_memory.search_topics("user1", "nonexistent", min_similarity=0.5)
        assert results == []

    def test_cosine_similarity_calculation(self):
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = ArchivalMemory._cosine_similarity(vec1, vec2)
        assert similarity == 0.0  # Orthogonal vectors

        vec1 = [1.0, 1.0, 1.0]
        vec2 = [1.0, 1.0, 1.0]
        similarity = ArchivalMemory._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)  # Identical vectors
