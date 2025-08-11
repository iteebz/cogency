"""Tool mock fixtures for testing."""

import pytest
from resilient_result import Result

from cogency.tools.base import Tool


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="Mock tool for testing",
            schema="mock_tool(arg='value')",
            emoji="🔧",
            examples=["mock_tool(arg='test')"],
            rules=["Mock tool for testing"],
        )

    async def run(self, **kwargs):
        return Result.ok(f"Mock tool called with {kwargs}")

    async def execute(self, **kwargs):
        return await self.run(**kwargs)


@pytest.fixture
def mock_tool():
    """Mock tool for testing."""
    return MockTool()


@pytest.fixture
def tools():
    """Mock tools fixture for testing."""
    return [MockTool()]
