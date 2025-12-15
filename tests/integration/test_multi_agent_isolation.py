import pytest

from cogency import Agent
from cogency.core.config import Security
from cogency.lib.sqlite import SQLite


@pytest.mark.asyncio
async def test_isolates_agents(tmp_path, mock_llm):
    run1_sandbox = tmp_path / "run1_sandbox"
    run1_sandbox.mkdir()
    run2_sandbox = tmp_path / "run2_sandbox"
    run2_sandbox.mkdir()

    agent1 = Agent(
        llm=mock_llm,
        storage=SQLite(db_path=str(tmp_path / "run1.db")),
        security=Security(access="sandbox", sandbox_dir=str(run1_sandbox)),
    )
    agent2 = Agent(
        llm=mock_llm,
        storage=SQLite(db_path=str(tmp_path / "run2.db")),
        security=Security(access="sandbox", sandbox_dir=str(run2_sandbox)),
    )

    write_tool_agent1 = next(t for t in agent1.config.tools if t.name == "write")
    create_result = await write_tool_agent1.execute(
        file="isolated_file.txt",
        content="content1",
        sandbox_dir=agent1.config.security.sandbox_dir,
        access=agent1.config.security.access,
    )
    assert "Wrote isolated_file.txt (+1/-0)" in create_result.outcome

    read_tool_agent2 = next(t for t in agent2.config.tools if t.name == "read")
    read_result_agent2 = await read_tool_agent2.execute(
        file="isolated_file.txt",
        sandbox_dir=agent2.config.security.sandbox_dir,
        access=agent2.config.security.access,
    )

    assert "not found" in read_result_agent2.outcome
    read_tool_agent1 = next(t for t in agent1.config.tools if t.name == "read")
    read_result_agent1 = await read_tool_agent1.execute(
        file="isolated_file.txt",
        sandbox_dir=agent1.config.security.sandbox_dir,
        access=agent1.config.security.access,
    )

    assert read_result_agent1.content is not None
    assert "content1" in read_result_agent1.content
