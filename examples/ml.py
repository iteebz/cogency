#!/usr/bin/env python3
"""ML - Machine learning with beautiful feedback."""

from cogency import Agent
from cogency.events import ConsoleHandler
from cogency.tools import Files

# ML agent with file tools
agent = Agent("ml", tools=[Files()], handlers=[ConsoleHandler()])
result = agent.run_sync("Create a simple scikit-learn classifier and save to ml_model.py")
print(f"\nModel created: {result[0]}")
