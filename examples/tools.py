#!/usr/bin/env python3
"""Tools - Watch agent use tools with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler
from cogency.tools import Files, Shell

# Agent with tools and beautiful console feedback
agent = Agent("assistant", tools=[Files(), Shell()], handlers=[ConsoleHandler()])
result = agent.run_sync("List all Python files in this directory")
print(f"\nResult: {result[0]}")
