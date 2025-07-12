"""Tests for BaseTool abstract base class."""

import pytest

from cogency.tools.base import BaseTool


class ConcreteTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""

    def __init__(self):
        super().__init__(name="test_tool", description="A test tool")

    def run(self, **kwargs):
        if "error" in kwargs:
            raise ValueError("Test error")
        return {"result": "success", "args": kwargs}

    def get_schema(self):
        return "test_tool(arg1=str, arg2=int)"

    def get_usage_examples(self):
        return ["test_tool(arg1='hello', arg2=42)"]


class TestBaseTool:
    """Test suite for BaseTool abstract base class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tool = ConcreteTool()

    def test_base_tool_initialization(self):
        """Test BaseTool initialization."""
        assert self.tool.name == "test_tool"
        assert self.tool.description == "A test tool"

    def test_validate_and_run_success(self):
        """Test successful validation and run."""
        result = self.tool.validate_and_run(arg1="test", arg2=123)

        assert result["result"] == "success"
        assert result["args"]["arg1"] == "test"
        assert result["args"]["arg2"] == 123

    def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = self.tool.validate_and_run(error=True)

        assert "error" in result
        assert result["error"] == "Test error"

    def test_abstract_methods(self):
        """Test that abstract methods are implemented."""
        # These should not raise NotImplementedError
        self.tool.run()
        self.tool.get_schema()
        self.tool.get_usage_examples()

    def test_base_tool_cannot_be_instantiated(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool("test", "description")

    def test_tool_name_attribute(self):
        """Test that tool has name attribute."""
        assert hasattr(self.tool, 'name')
        assert isinstance(self.tool.name, str)
        assert len(self.tool.name) > 0

    def test_tool_description_attribute(self):
        """Test that tool has description attribute.""" 
        assert hasattr(self.tool, 'description')
        assert isinstance(self.tool.description, str)
        assert len(self.tool.description) > 0

    def test_schema_format(self):
        """Test that schema follows expected format."""
        schema = self.tool.get_schema()
        assert isinstance(schema, str)
        assert self.tool.name in schema
        assert "(" in schema and ")" in schema

    def test_usage_examples_format(self):
        """Test that usage examples follow expected format."""
        examples = self.tool.get_usage_examples()
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(example, str) for example in examples)
        assert all(self.tool.name in example for example in examples)

    def test_run_returns_dict(self):
        """Test that run method returns a dictionary."""
        result = self.tool.run()
        assert isinstance(result, dict)

    def test_validate_and_run_returns_dict(self):
        """Test that validate_and_run method returns a dictionary."""
        result = self.tool.validate_and_run()
        assert isinstance(result, dict)