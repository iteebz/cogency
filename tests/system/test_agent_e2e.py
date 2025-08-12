"""System tests - Real LLM calls, expensive and minimal."""

import os
from pathlib import Path

import pytest

from cogency import Agent

# Skip all system tests if no API keys available
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
has_api_keys = bool(openai_key and openai_key != "test-key") or bool(
    anthropic_key and anthropic_key != "test-key"
)


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.skipif(not has_api_keys, reason="Requires real API keys")
@pytest.mark.asyncio
async def test_agent_basic_response():
    """Real LLM call - validates full Agent → LLM → Response flow."""
    agent = Agent("assistant")

    response = await agent.run_async("What is 2 + 2?")

    assert isinstance(response, str)
    assert len(response) > 0
    assert "4" in response


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.skipif(not has_api_keys, reason="Requires real API keys")
@pytest.mark.asyncio
async def test_agent_file_creation():
    """Real LLM + Files tool - validates Agent → LLM → Tool → File system flow."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        agent = Agent("assistant", tools=["files"])

        response = await agent.run_async(
            "Create a file called hello.txt with the content 'Hello World'"
        )

        hello_file = Path("hello.txt")
        assert hello_file.exists(), f"File not created. Response: {response}"
        assert "Hello World" in hello_file.read_text()


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.skipif(not has_api_keys, reason="Requires real API keys")
@pytest.mark.asyncio
async def test_agent_shell_execution():
    """Real LLM + Shell tool - validates Agent → LLM → Shell → Output flow."""
    agent = Agent("assistant", tools=["shell"])

    response = await agent.run_async("Run the command 'echo testing123' and show me the output")

    assert "testing123" in response.lower()


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.skipif(not has_api_keys, reason="Requires real API keys")
@pytest.mark.asyncio
async def test_agent_with_memory():
    """Real LLM + Memory - validates Agent → LLM → Memory persistence flow."""
    agent = Agent("assistant", memory=True)

    # First interaction - store information
    response1 = await agent.run_async("Remember that my favorite color is blue")
    assert isinstance(response1, str)

    # Second interaction - recall information
    response2 = await agent.run_async("What is my favorite color?")
    assert "blue" in response2.lower()


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.skipif(not has_api_keys, reason="Requires real API keys")
@pytest.mark.asyncio
async def test_agent_complex_workflow():
    """Real LLM + Multiple tools - validates full system integration."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        agent = Agent("assistant", tools=["files", "shell"], memory=True)

        response = await agent.run_async(
            "Create a Python script that prints 'System test passed', then run it and remember the result"
        )

        # Should have created and executed file
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify some evidence of execution occurred
        assert "system test passed" in response.lower() or "passed" in response.lower()
