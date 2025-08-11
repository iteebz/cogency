"""Unit tests for archive pure functions - core business logic only."""

import tempfile
from unittest.mock import AsyncMock

import pytest
from resilient_result import Ok

from cogency.memory.archive import search, storage
from cogency.memory.archive.types import TopicArtifact


def test_artifact_creation():
    """Test basic artifact creation."""
    artifact = TopicArtifact("Python", "List comprehensions are fast")
    assert artifact.topic == "Python"
    assert artifact.content == "List comprehensions are fast"
    assert artifact.source_conversations == []
    assert isinstance(artifact.created, str)
    assert isinstance(artifact.updated, str)


def test_artifact_with_metadata():
    """Test artifact creation with metadata."""
    metadata = {"created": "2024-01-01T00:00:00", "source_conversations": ["conv1", "conv2"]}
    artifact = TopicArtifact("Python", "Fast code", metadata=metadata)

    assert artifact.created == "2024-01-01T00:00:00"
    assert artifact.source_conversations == ["conv1", "conv2"]


def test_to_markdown():
    """Test markdown generation with frontmatter."""
    artifact = TopicArtifact("Python", "Fast code")
    artifact.source_conversations = ["conv1"]

    markdown = storage.to_markdown(artifact)

    assert markdown.startswith("---\n")
    assert "topic: Python" in markdown
    assert "source_conversations:\n- conv1" in markdown
    assert "Fast code" in markdown


def test_from_markdown():
    """Test markdown parsing with frontmatter."""
    markdown = """---
topic: Python
created: 2024-01-01T00:00:00
updated: 2024-01-02T00:00:00
source_conversations:
- conv1
- conv2
---

# Python Performance

List comprehensions are faster than for loops."""

    artifact = storage.from_markdown("Python", markdown)

    assert artifact.topic == "Python"
    # YAML parser converts ISO strings to datetime objects - accept both formats
    assert (
        str(artifact.created) == "2024-01-01 00:00:00" or artifact.created == "2024-01-01T00:00:00"
    )
    assert artifact.source_conversations == ["conv1", "conv2"]
    assert "# Python Performance" in artifact.content
    assert "List comprehensions are faster" in artifact.content


def test_from_markdown_no_frontmatter():
    """Test markdown parsing without frontmatter."""
    markdown = "Just plain content"
    artifact = storage.from_markdown("Topic", markdown)

    assert artifact.topic == "Topic"
    assert artifact.content == "Just plain content"


def test_user_path():
    """Test user directory path generation."""
    path = storage.get_user_path("user123", "/tmp/test")
    assert str(path).endswith("user123/topics")


def test_topic_path_sanitization():
    """Test topic filename sanitization - prevents directory traversal."""
    # Test dangerous characters are sanitized
    path = storage.get_topic_path("user1", "Python/Performance & <Tips>", "/tmp")
    assert path.name == "pythonperformance--tips.md"

    # Test spaces become hyphens
    path = storage.get_topic_path("user1", "Python Performance", "/tmp")
    assert path.name == "python-performance.md"


def test_cosine_identical():
    """Test identical vectors return 1.0."""
    vec = [1.0, 1.0, 1.0]
    similarity = search.cosine_similarity(vec, vec)
    assert similarity == pytest.approx(1.0)


def test_cosine_orthogonal():
    """Test orthogonal vectors return 0.0."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    similarity = search.cosine_similarity(vec1, vec2)
    assert similarity == 0.0


def test_cosine_zero_magnitude():
    """Test zero vectors return 0.0."""
    vec1 = [0.0, 0.0, 0.0]
    vec2 = [1.0, 1.0, 1.0]
    similarity = search.cosine_similarity(vec1, vec2)
    assert similarity == 0.0


def test_cosine_different_lengths():
    """Test different length vectors return 0.0."""
    vec1 = [1.0, 1.0]
    vec2 = [1.0, 1.0, 1.0]
    similarity = search.cosine_similarity(vec1, vec2)
    assert similarity == 0.0


@pytest.mark.asyncio
async def test_store_knowledge():
    """Test knowledge storage workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = await storage.store_knowledge(
            "user1",
            "Python",
            "List comprehensions are fast",
            conversation_id="conv1",
            base_path=temp_dir,
        )

        assert result.success
        assert result.data["topic"] == "Python"

        # Verify file was created
        topic_path = storage.get_topic_path("user1", "Python", temp_dir)
        assert topic_path.exists()

        # Verify content
        content = topic_path.read_text()
        assert "List comprehensions are fast" in content
        assert "conv1" in content


@pytest.mark.asyncio
async def test_load_topic():
    """Test topic loading from filesystem."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Store first
        await storage.store_knowledge("user1", "Python", "Fast code", base_path=temp_dir)

        # Load and verify
        artifact = await storage.load_topic("user1", "Python", temp_dir)
        assert artifact is not None
        assert artifact.topic == "Python"
        assert artifact.content == "Fast code"


@pytest.mark.asyncio
async def test_load_nonexistent():
    """Test loading non-existent topic returns None."""
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = await storage.load_topic("user1", "NonExistent", temp_dir)
        assert artifact is None


@pytest.fixture
def mock_embed_provider():
    """Mock embedding provider."""
    provider = AsyncMock()
    provider.embed.return_value = Ok([[0.1, 0.2, 0.3]])
    return provider


@pytest.fixture
def sample_cache():
    """Sample embedding cache."""
    return {
        "user1:Python": {
            "embedding": [0.1, 0.2, 0.3],
            "content": "List comprehensions are fast",
            "topic": "Python",
            "updated": "2024-01-01T00:00:00",
        },
        "user1:JavaScript": {
            "embedding": [0.9, 0.1, 0.1],
            "content": "Arrow functions are concise",
            "topic": "JavaScript",
            "updated": "2024-01-02T00:00:00",
        },
    }


@pytest.mark.asyncio
async def test_search_with_results(mock_embed_provider, sample_cache):
    """Test search returning results above similarity threshold."""
    results = await search.search_topics(
        mock_embed_provider,
        "user1",
        "Python performance",
        sample_cache,
        limit=5,
        min_similarity=0.1,
    )

    assert len(results) > 0
    assert all("topic" in result for result in results)
    assert all("similarity" in result for result in results)


@pytest.mark.asyncio
async def test_search_no_results(mock_embed_provider):
    """Test search with empty cache returns no results."""
    results = await search.search_topics(mock_embed_provider, "user1", "query", {}, limit=5)

    assert results == []


@pytest.mark.asyncio
async def test_search_user_isolation(mock_embed_provider, sample_cache):
    """Test search only returns results for specified user."""
    # Add data for different user
    sample_cache["user2:Python"] = {
        "embedding": [0.1, 0.2, 0.3],
        "content": "Different user content",
        "topic": "Python",
        "updated": "2024-01-01T00:00:00",
    }

    results = await search.search_topics(
        mock_embed_provider, "user1", "Python", sample_cache, min_similarity=0.1
    )

    # Should only return user1's results
    user1_results = [r for r in results if "Different user" not in r["content"]]
    assert len(user1_results) == len(results)
