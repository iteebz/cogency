#!/usr/bin/env python3
"""Hello World - Cogency's adaptive intelligence in 5 lines."""

from cogency import Agent, Files, Shell

agent = Agent("assistant", tools=[Files(), Shell()])

# Simple → instant response (no tools needed)
print("Simple:", agent.run("What's 15 * 23?"))

# Complex → full reasoning automatically
print("Complex:", agent.run("Build a URL shortener with FastAPI"))
