"""Tools tests - First principles V3 launch coverage."""

import pytest

from cogency import TOOLS, Tool


def test_exist():
    """Basic tools are available."""
    assert len(TOOLS) > 0

    # All items are tools
    for tool in TOOLS:
        assert isinstance(tool, Tool)
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "execute")


def test_file_tools():
    """File tools are present and functional."""
    tool_names = {t.name for t in TOOLS}

    # Should have list, read, write (short names)
    assert "list" in tool_names
    assert "read" in tool_names
    assert "write" in tool_names


@pytest.mark.asyncio
async def test_file_list_execution():
    """File list tool executes without crashing."""
    file_list_tool = next((t for t in TOOLS if "list" in t.name.lower()), None)
    assert file_list_tool is not None

    # Should execute without crashing
    result = await file_list_tool.execute()

    # Result should have success/failure pattern
    assert hasattr(result, "success") or hasattr(result, "failure")


def test_web_tools():
    """Web tools are present."""
    web_tools = [t for t in TOOLS if any(web in t.name.lower() for web in ["search", "scrape"])]
    assert len(web_tools) > 0

    # Should have search and/or scrape
    tool_names = {t.name for t in web_tools}
    assert any("search" in name for name in tool_names) or any(
        "scrape" in name for name in tool_names
    )


def test_shell_tools():
    """Shell tools are present."""
    shell_tools = [t for t in TOOLS if "shell" in t.name.lower()]
    assert len(shell_tools) > 0
