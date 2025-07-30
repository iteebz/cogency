"""Unit tests for LLM-native Memory system."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.memory import Memory


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = Mock()
    llm.complete = AsyncMock(return_value="Synthesized impression")
    return llm


@pytest.fixture
def memory(mock_llm):
    """Memory instance for testing."""
    return Memory(mock_llm)


@pytest.mark.asyncio
async def test_remember_human(memory):
    """Remember human content with weighting."""
    await memory.remember("I prefer TypeScript", human=True)

    assert "[HUMAN] I prefer TypeScript" in memory.recent
    assert memory.impression == ""


@pytest.mark.asyncio
async def test_remember_agent(memory):
    """Remember agent content with weighting."""
    await memory.remember("User seems experienced", human=False)

    assert "[AGENT] User seems experienced" in memory.recent
    assert memory.impression == ""


@pytest.mark.asyncio
async def test_recall_empty(memory):
    """Recall returns empty string when no content."""
    result = await memory.recall()
    assert result == ""


@pytest.mark.asyncio
async def test_recall_recent_only(memory):
    """Recall formats recent interactions only."""
    await memory.remember("I like Python", human=True)

    result = await memory.recall()
    assert "RECENT INTERACTIONS:" in result
    assert "[HUMAN] I like Python" in result


@pytest.mark.asyncio
async def test_recall_impression_only(memory):
    """Recall formats impression only."""
    memory.impression = "User prefers functional programming"

    result = await memory.recall()
    assert "USER IMPRESSION:" in result
    assert "User prefers functional programming" in result


@pytest.mark.asyncio
async def test_recall_both(memory):
    """Recall formats both impression and recent."""
    memory.impression = "User likes TypeScript"
    await memory.remember("Working on React project", human=True)

    result = await memory.recall()
    assert "USER IMPRESSION:" in result
    assert "RECENT INTERACTIONS:" in result
    assert "User likes TypeScript" in result
    assert "[HUMAN] Working on React project" in result


@pytest.mark.asyncio
async def test_synthesis_triggers(memory, mock_llm):
    """Synthesis triggers at threshold."""
    memory.synthesis_threshold = 50

    long_content = "x" * 60
    await memory.remember(long_content, human=True)

    mock_llm.complete.assert_called_once()
    assert memory.impression == "Synthesized impression"
    assert memory.recent == ""


@pytest.mark.asyncio
async def test_synthesis_builds_on_existing(memory, mock_llm):
    """Synthesis includes existing impression."""
    memory.impression = "Existing impression"
    memory.synthesis_threshold = 50

    long_content = "x" * 60
    await memory.remember(long_content, human=True)

    call_args = mock_llm.complete.call_args[0][0]
    assert "Current Impression: Existing impression" in call_args
    assert f"Recent Interactions: \n[HUMAN] {long_content}" in call_args


@pytest.mark.asyncio
async def test_human_weighting_preserved(memory):
    """Human vs agent weighting preserved."""
    await memory.remember("Human preference", human=True)
    await memory.remember("Agent observation", human=False)

    result = await memory.recall()
    assert "[HUMAN] Human preference" in result
    assert "[AGENT] Agent observation" in result


@pytest.mark.asyncio
async def test_synthesis_prompt_format(memory, mock_llm):
    """Synthesis prompt contains required elements."""
    memory.synthesis_threshold = 10
    await memory.remember("test", human=True)

    call_args = mock_llm.complete.call_args[0][0]
    assert "Form a refined impression" in call_args
    assert "Captures essential preferences" in call_args
    assert "Prioritizes human statements" in call_args
    assert "Eliminates contradictions" in call_args


@pytest.mark.asyncio
async def test_no_synthesis_on_empty(memory, mock_llm):
    """No synthesis on empty recent content."""
    memory.recent = ""
    await memory._synthesize()

    mock_llm.complete.assert_not_called()
    assert memory.impression == ""
