"""Examples integration tests - ZERO BULLSHIT."""
import os
import subprocess
import pytest


class TestExamples:
    """Test that examples actually work."""
    
    @pytest.mark.skipif(
        not any(os.getenv(key) for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]),
        reason="No API key configured for LLM"
    )
    def test_basic_usage_example(self):
        """Basic usage example runs without errors."""
        result = subprocess.run(
            ["poetry", "run", "python", "examples/basic_usage.py"],
            cwd="/Users/teebz/dev/workspace/cogency",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Example failed: {result.stderr}"
        assert "Response:" in result.stdout
    
    def test_custom_tool_example(self):
        """Custom tool example runs without errors."""
        result = subprocess.run(
            ["poetry", "run", "python", "examples/custom_tool.py"],
            cwd="/Users/teebz/dev/workspace/cogency",
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Example failed: {result.stderr}"
        assert len(result.stdout) > 0