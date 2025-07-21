"""Test tool auto-discovery and registration."""
import pytest

from cogency.tools.base import BaseTool


class TestToolRegistry:
    """Test tool auto-discovery and registration."""
    
    def test_tool_decorator_registration(self):
        """@tool decorator should register tools."""
        from cogency.tools.registry import get_tools
        
        tools = get_tools()
        tool_names = [t.name for t in tools]
        
        # Calculator should be auto-registered via @tool decorator
        assert "calculator" in tool_names
    
    def test_tool_discovery_contract(self):
        """All registered tools should follow contracts."""
        from cogency.tools.registry import get_tools
        
        tools = get_tools()
        
        for tool in tools:
            # Must inherit from BaseTool
            assert isinstance(tool, BaseTool)
            
            # Must have required attributes
            assert hasattr(tool, 'name') and tool.name
            assert hasattr(tool, 'description') and tool.description
            
            # Schema must be informative
            schema = tool.schema()
            assert len(schema) > 20  # Non-trivial schema
            
            # Must have examples
            examples = tool.examples()
            assert len(examples) > 0