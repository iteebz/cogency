"""Tests for knowledge CLI commands."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from cogency.cli.knowledge import (
    export_knowledge,
    knowledge_command,
    knowledge_stats,
    prune_knowledge,
    search_knowledge,
)


@pytest.mark.asyncio
async def test_knowledge_command_search():
    """Test knowledge search command routing."""
    with patch("cogency.cli.knowledge.search_knowledge") as mock_search:
        await knowledge_command("search", "test query")
        mock_search.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_knowledge_command_stats():
    """Test knowledge stats command routing."""
    with patch("cogency.cli.knowledge.knowledge_stats") as mock_stats:
        await knowledge_command("stats")
        mock_stats.assert_called_once()


@pytest.mark.asyncio
async def test_knowledge_command_export():
    """Test knowledge export command routing."""
    with patch("cogency.cli.knowledge.export_knowledge") as mock_export:
        await knowledge_command("export", format="json")
        mock_export.assert_called_once_with("json")


@pytest.mark.asyncio
async def test_knowledge_command_prune():
    """Test knowledge prune command routing."""
    with patch("cogency.cli.knowledge.prune_knowledge") as mock_prune:
        await knowledge_command("prune", days=30)
        mock_prune.assert_called_once_with(30)


@pytest.mark.asyncio
async def test_search_knowledge_empty_results(capsys):
    """Test knowledge search with no results."""
    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = []

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        await search_knowledge("nonexistent query")

    captured = capsys.readouterr()
    assert "No knowledge found matching your query" in captured.out


@pytest.mark.asyncio
async def test_search_knowledge_with_results(capsys):
    """Test knowledge search with results."""
    from cogency.knowledge import KnowledgeArtifact

    # Create mock artifacts
    artifact1 = KnowledgeArtifact(
        topic="Python Basics",
        content="Python is a programming language",
        confidence=0.9,
        context="Programming tutorial",
        user_id="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = [artifact1]

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        await search_knowledge("python")

    captured = capsys.readouterr()
    assert "Found 1 relevant knowledge artifacts" in captured.out
    assert "Python Basics" in captured.out
    assert "90%" in captured.out  # Confidence percentage


@pytest.mark.asyncio
async def test_knowledge_stats_empty(capsys):
    """Test knowledge stats with no artifacts."""
    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = []

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        await knowledge_stats()

    captured = capsys.readouterr()
    assert "No knowledge artifacts found" in captured.out


@pytest.mark.asyncio
async def test_knowledge_stats_with_data(capsys):
    """Test knowledge stats with data."""
    from cogency.knowledge import KnowledgeArtifact

    # Create mock artifacts with different confidence levels
    artifacts = [
        KnowledgeArtifact(
            topic="High Confidence",
            content="Content 1",
            confidence=0.9,
            user_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        KnowledgeArtifact(
            topic="Medium Confidence",
            content="Content 2",
            confidence=0.6,
            user_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = artifacts

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        await knowledge_stats()

    captured = capsys.readouterr()
    assert "Knowledge Base Statistics" in captured.out
    assert "Total artifacts: 2" in captured.out
    assert "Unique topics: 2" in captured.out
    assert "High (80%+):" in captured.out
    assert "Medium (50%+):" in captured.out


@pytest.mark.asyncio
async def test_export_knowledge_json(capsys):
    """Test knowledge export as JSON."""
    from cogency.knowledge import KnowledgeArtifact

    artifact = KnowledgeArtifact(
        topic="Test Topic",
        content="Test content",
        confidence=0.8,
        user_id="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = [artifact]

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        with patch("builtins.open", create=True) as mock_file:
            await export_knowledge("json")

    captured = capsys.readouterr()
    assert "Knowledge exported successfully" in captured.out
    assert "Exported 1 artifacts" in captured.out
    mock_file.assert_called_once()


@pytest.mark.asyncio
async def test_prune_knowledge_no_candidates(capsys):
    """Test knowledge pruning with no candidates."""
    from cogency.knowledge import KnowledgeArtifact

    # Create recent, high-confidence artifact
    artifact = KnowledgeArtifact(
        topic="Recent Knowledge",
        content="Recent content",
        confidence=0.9,
        user_id="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = [artifact]

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        await prune_knowledge(30)

    captured = capsys.readouterr()
    assert "No knowledge needs pruning" in captured.out


@pytest.mark.asyncio
async def test_prune_knowledge_with_candidates(capsys):
    """Test knowledge pruning with candidates."""
    from datetime import timedelta

    from cogency.knowledge import KnowledgeArtifact

    # Create old, low-confidence artifact
    old_date = datetime.now() - timedelta(days=40)
    artifact = KnowledgeArtifact(
        topic="Old Knowledge",
        content="Old content",
        confidence=0.4,  # Low confidence
        user_id="test",
        created_at=old_date,
        updated_at=old_date,
    )

    mock_store = AsyncMock()
    mock_store.search_knowledge.return_value = [artifact]

    with patch("cogency.cli.knowledge.SQLite", return_value=mock_store):
        with patch("builtins.input", return_value="n"):  # Cancel pruning
            await prune_knowledge(30)

    captured = capsys.readouterr()
    assert "Found 1 artifacts to prune" in captured.out
    assert "Pruning cancelled" in captured.out
