#!/usr/bin/env python3
"""Hello World - Cogency's adaptive intelligence in 5 lines."""

from cogency import Agent, filesystem_tools

agent = Agent("assistant", tools=filesystem_tools())

# Simple → instant response (no tools needed)
print("Simple:", agent.run("What's 15 * 23?"))

# Complex → full reasoning automatically
print("Complex:", agent.run("Build a URL shortener with FastAPI"))
