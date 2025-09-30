"""Pragmatic test for base_dir isolation contract."""

import pytest

from cogency import Agent
from cogency.core.protocols import LLM


# Define a compliant mock LLM for testing
class MockLLM(LLM):
    async def stream(self, messages):
        yield

    async def generate(self, messages):
        return ""

    async def connect(self, messages):
        return self

    async def send(self, content):
        yield

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_base_dir_isolates_runs(tmp_path):
    """Verify that two agents with different base_dirs have isolated sandboxes."""
    # Create two separate base directories
    run1_dir = tmp_path / "run1"
    run1_dir.mkdir()
    run2_dir = tmp_path / "run2"
    run2_dir.mkdir()

    # Instantiate two agents with different base_dirs
    agent1 = Agent(llm=MockLLM(), base_dir=str(run1_dir))
    agent2 = Agent(llm=MockLLM(), base_dir=str(run2_dir))

    # Agent 1 creates a file in its sandbox using the file_write tool
    write_tool_agent1 = next(t for t in agent1.config.tools if t.name == "file_write")
    create_result = await write_tool_agent1.execute(
        file="isolated_file.txt", 
        content="content1",
        base_dir=agent1.config.base_dir,
        access=agent1.config.security.access
    )
    assert "Created isolated_file.txt" in create_result.outcome

    # Agent 2 tries to read the file created by Agent 1
    read_tool_agent2 = next(t for t in agent2.config.tools if t.name == "file_read")
    read_result_agent2 = await read_tool_agent2.execute(
        "isolated_file.txt",
        base_dir=agent2.config.base_dir,
        access=agent2.config.security.access
    )

    # Assert that Agent 2 CANNOT find the file, proving isolation
    assert "File 'isolated_file.txt' does not exist" in read_result_agent2.outcome

    # Agent 1 reads the file it created to ensure it has access to its own sandbox
    read_tool_agent1 = next(t for t in agent1.config.tools if t.name == "file_read")
    read_result_agent1 = await read_tool_agent1.execute(
        "isolated_file.txt",
        base_dir=agent1.config.base_dir,
        access=agent1.config.security.access
    )

    # Assert that Agent 1 CAN read its own file
    assert "content1" in read_result_agent1.content
