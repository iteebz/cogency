#!/usr/bin/env python3
"""Coder - Watch agent write code with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler
from cogency.tools import Files

# Coding agent with file tools
agent = Agent("coder", tools=[Files()], handlers=[ConsoleHandler()])
result = agent.run_sync("Create a simple HTTP server in Python and save it to server.py")
print(f"\nCode created: {result[0]}")
