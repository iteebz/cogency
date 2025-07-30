"""Tool registry tests."""

import os
from unittest.mock import MagicMock, patch

from cogency.tools.base import Tool
from cogency.tools.files import Files
from cogency.tools.registry import build_registry


def test_register():
    from cogency.tools.registry import get_tools

    tools = get_tools()
    tool_names = [t.name for t in tools]

    assert "calculator" in tool_names


def test_discover():
    from cogency.tools.registry import get_tools

    tools = get_tools()

    for tool in tools:
        assert isinstance(tool, Tool)
        assert hasattr(tool, "name") and tool.name
        assert hasattr(tool, "description") and tool.description

        schema = tool.schema
        assert len(schema) > 0

        examples = tool.examples
        assert len(examples) > 0
