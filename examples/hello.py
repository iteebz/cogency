#!/usr/bin/env python3
"""Hello World - Pure intelligence, zero ceremony."""

from cogency import Agent
from cogency.events import ConsoleHandler

# Pure intelligence - beautiful console feedback, no ceremony
agent = Agent("assistant", handlers=[ConsoleHandler()])
result = agent.run_sync("Explain quantum computing in simple terms")
print(result[0])
