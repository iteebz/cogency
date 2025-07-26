"""Tool registry tests."""

import os
from unittest.mock import MagicMock, patch

from cogency.tools.base import BaseTool
from cogency.tools.files import Files
from cogency.tools.registry import build_registry


def test_decorator_registration():
    from cogency.tools.registry import get_tools

    tools = get_tools()
    tool_names = [t.name for t in tools]

    assert "calculator" in tool_names


def test_discovery_contract():
    from cogency.tools.registry import get_tools

    tools = get_tools()

    for tool in tools:
        assert isinstance(tool, BaseTool)
        assert hasattr(tool, "name") and tool.name
        assert hasattr(tool, "description") and tool.description

        schema = tool.schema
        assert len(schema) > 20

        examples = tool.examples
        assert len(examples) > 0
