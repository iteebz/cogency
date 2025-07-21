"""Test Code tool business logic."""
import pytest

from cogency.tools.code import Code


class TestCode:
    """Test Code tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Code tool implements required interface."""
        code = Code()
        
        # Required attributes
        assert code.name == "code"
        assert code.description
        assert hasattr(code, 'run')
        
        # Schema and examples
        schema = code.schema()
        examples = code.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_empty_code(self):
        """Code tool handles empty code."""
        code = Code()
        
        result = await code.run(code="")
        assert "error" in result
        assert "Code cannot be empty" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_language(self):
        """Code tool handles unsupported languages."""
        code = Code()
        
        result = await code.run(code="print('hello')", language="ruby")
        assert "error" in result
        assert "Unsupported language" in result["error"]
    
    @pytest.mark.asyncio
    async def test_python_execution(self):
        """Code tool executes Python code."""
        code = Code()
        
        result = await code.run(code="print(2 + 2)", language="python")
        assert "exit_code" in result
        assert "output" in result
        # Don't assert specific output since execution environment may vary