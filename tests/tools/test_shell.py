"""Test Shell tool business logic."""
import pytest

from cogency.tools.shell import Shell


class TestShell:
    """Test Shell tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Shell tool implements required interface."""
        shell = Shell()
        
        # Required attributes
        assert shell.name == "shell"
        assert shell.description
        assert hasattr(shell, 'run')
        
        # Schema and examples
        schema = shell.schema()
        examples = shell.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_empty_command(self):
        """Shell tool handles empty commands."""
        shell = Shell()
        
        result = await shell.run(command="")
        assert "error" in result
        assert "Command cannot be empty" in result["error"]
    
    @pytest.mark.asyncio
    async def test_blocked_command(self):
        """Shell tool blocks dangerous commands."""
        shell = Shell()
        
        result = await shell.run(command="rm -rf /")
        assert "error" in result
        assert "blocked for security" in result["error"]
    
    @pytest.mark.asyncio
    async def test_safe_command(self):
        """Shell tool executes safe commands."""
        shell = Shell()
        
        result = await shell.run(command="echo hello")
        assert "exit_code" in result
        assert result["success"] == (result["exit_code"] == 0)
        assert "stdout" in result
        assert "stderr" in result