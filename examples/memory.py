#!/usr/bin/env python3
"""Memory - Persistent context with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler

# Agent with memory and console feedback
agent = Agent("assistant", memory=True, handlers=[ConsoleHandler()])

# Set context
response1, conv_id = agent.run_sync("I work with Python web frameworks. Remember this.")
print(f"Context set: {response1[0]}")

# Test memory
response2, _ = agent.run_sync("What do I work with?", conversation_id=conv_id)
print(f"Memory recall: {response2}")
