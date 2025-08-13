"""Tests for memory CLI commands."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.cli.memory import (
    clear_memory,
    export_memory,
    memory_command,
    memory_stats,
    show_memory,
)


@pytest.mark.asyncio
async def test_memory_command_clear():
    """Test memory clear command routing."""
    with patch("cogency.cli.memory.clear_memory") as mock_clear:
        await memory_command("clear")
        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_memory_command_show():
    """Test memory show command routing."""
    with patch("cogency.cli.memory.show_memory") as mock_show:
        await memory_command("show", raw=True)
        mock_show.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_memory_command_export():
    """Test memory export command routing."""
    with patch("cogency.cli.memory.export_memory") as mock_export:
        await memory_command("export", "test-conv-id")
        mock_export.assert_called_once_with("test-conv-id")


@pytest.mark.asyncio
async def test_memory_command_export_missing_id(capsys):
    """Test memory export without conversation ID."""
    await memory_command("export")

    captured = capsys.readouterr()
    assert "Error: --conversation-id required for export" in captured.out


@pytest.mark.asyncio
async def test_clear_memory_no_runtime_profile(capsys):
    """Test clearing memory when no runtime profile exists."""
    mock_memory = MagicMock()
    mock_memory._system._profiles = {}

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = None

    with patch("cogency.cli.memory.Memory", return_value=mock_memory):
        with patch("cogency.cli.memory.SQLite", return_value=mock_store):
            await clear_memory()

    captured = capsys.readouterr()
    assert "No runtime profile found" in captured.out
    assert "Memory context cleared successfully" in captured.out


@pytest.mark.asyncio
async def test_clear_memory_with_runtime_profile(capsys):
    """Test clearing memory when runtime profile exists."""
    mock_memory = MagicMock()
    mock_memory._system._profiles = {"default": MagicMock()}

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = None

    with patch("cogency.cli.memory.Memory", return_value=mock_memory):
        with patch("cogency.cli.memory.SQLite", return_value=mock_store):
            await clear_memory()

    captured = capsys.readouterr()
    assert "Cleared runtime profile for user: default" in captured.out


@pytest.mark.asyncio
async def test_show_memory_no_profile(capsys):
    """Test showing memory when no profile exists."""
    mock_memory = MagicMock()
    mock_memory._system._profiles = {}

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = None

    with patch("cogency.cli.memory.Memory", return_value=mock_memory):
        with patch("cogency.cli.memory.SQLite", return_value=mock_store):
            await show_memory()

    captured = capsys.readouterr()
    assert "No runtime profile loaded" in captured.out
    assert "No persistent profile found" in captured.out


@pytest.mark.asyncio
async def test_show_memory_with_profile(capsys):
    """Test showing memory with existing profile."""
    from cogency.memory.memory import Profile

    # Create mock profile
    profile = Profile(
        user_id="test",
        preferences={"name": "Test User"},
        goals=["Learn Python"],
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    mock_memory = MagicMock()
    mock_memory._system._profiles = {}

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = profile

    with patch("cogency.cli.memory.Memory", return_value=mock_memory):
        with patch("cogency.cli.memory.SQLite", return_value=mock_store):
            await show_memory()

    captured = capsys.readouterr()
    assert "Memory Content:" in captured.out
    assert "Profile Metadata:" in captured.out
    assert "User ID: test" in captured.out


@pytest.mark.asyncio
async def test_show_memory_raw_format(capsys):
    """Test showing memory in raw format."""
    from cogency.memory.memory import Profile

    profile = Profile(
        user_id="test",
        preferences={"name": "Test User"},
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    mock_memory = MagicMock()
    mock_memory._system._profiles = {}

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = profile

    with patch("cogency.cli.memory.Memory", return_value=mock_memory):
        with patch("cogency.cli.memory.SQLite", return_value=mock_store):
            await show_memory(raw=True)

    captured = capsys.readouterr()
    assert "Raw Storage Format:" in captured.out


@pytest.mark.asyncio
async def test_export_memory_conversation_not_found(capsys):
    """Test exporting memory for non-existent conversation."""
    mock_store = AsyncMock()
    mock_store.load_conversation.return_value = None

    with patch("cogency.cli.memory.SQLite", return_value=mock_store):
        await export_memory("nonexistent-id")

    captured = capsys.readouterr()
    assert "Conversation nonexist... not found" in captured.out


@pytest.mark.asyncio
async def test_export_memory_success(capsys):
    """Test successful memory export."""
    from cogency.memory.memory import Profile
    from cogency.state import Conversation

    # Create mock conversation
    conversation = Conversation(
        user_id="test", messages=[{"role": "user", "content": "Hello"}], last_updated=datetime.now()
    )

    # Create mock profile
    profile = Profile(
        user_id="test",
        preferences={"name": "Test User"},
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    mock_store = AsyncMock()
    mock_store.load_conversation.return_value = conversation
    mock_store.load_profile.return_value = profile

    with patch("cogency.cli.memory.SQLite", return_value=mock_store):
        with patch("builtins.open", create=True) as mock_file:
            await export_memory("test-conv-id")

    captured = capsys.readouterr()
    assert "Memory exported successfully" in captured.out
    assert "Messages: 1" in captured.out
    mock_file.assert_called_once()


@pytest.mark.asyncio
async def test_memory_stats_no_profile(capsys):
    """Test memory stats when no profile exists."""
    mock_store = AsyncMock()
    mock_store.load_profile.return_value = None

    with patch("cogency.cli.memory.SQLite", return_value=mock_store):
        await memory_stats()

    captured = capsys.readouterr()
    assert "No memory profile found" in captured.out


@pytest.mark.asyncio
async def test_memory_stats_with_profile(capsys):
    """Test memory stats with existing profile."""
    from datetime import timedelta

    from cogency.memory.memory import Profile

    # Create profile with some age
    created_date = datetime.now() - timedelta(days=10)
    updated_date = datetime.now() - timedelta(days=2)

    profile = Profile(
        user_id="test",
        preferences={"name": "Test User", "language": "Python"},
        goals=["Learn AI", "Build apps"],
        expertise_areas=["Python", "ML"],
        created_at=created_date,
        last_updated=updated_date,
    )

    mock_store = AsyncMock()
    mock_store.load_profile.return_value = profile

    with patch("cogency.cli.memory.SQLite", return_value=mock_store):
        await memory_stats()

    captured = capsys.readouterr()
    assert "Memory System Statistics" in captured.out
    assert "Profile age: 10 days" in captured.out
    assert "Last updated: 2 days ago" in captured.out
    assert "Preferences: 2 items" in captured.out
    assert "Goals: 2 items" in captured.out
    assert "Expertise areas: 2 items" in captured.out
    assert "Recent Preferences:" in captured.out
    assert "Current Goals:" in captured.out
