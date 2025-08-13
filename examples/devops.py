#!/usr/bin/env python3
"""DevOps - Infrastructure automation with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler
from cogency.tools import Files, Shell

# DevOps agent with system tools
agent = Agent("devops", tools=[Files(), Shell()], handlers=[ConsoleHandler()])
result = agent.run_sync("Create a Dockerfile for a Python Flask app")
print(f"\nInfrastructure created: {result[0]}")
