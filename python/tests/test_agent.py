from cogency import Agent


def test_agent_run():
    agent = Agent(name="TestAgent")
    result = agent.run(task="test task")
    assert result == "Agent TestAgent is running task: test task"
