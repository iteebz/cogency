#!/usr/bin/env python3
"""Research - Web search with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler
from cogency.tools import Search

# Research agent with search tools
agent = Agent("researcher", tools=[Search()], handlers=[ConsoleHandler()])
result = agent.run_sync("Find the latest Python 3.13 release notes")
print(f"\nResearch results: {result[0]}")
