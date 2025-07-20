#!/usr/bin/env python3
"""Coding demo agent - like Cursor/Claude Code but in cogency."""
import asyncio
from cogency import Agent
from cogency.tools import Shell, Files, Code

async def main():
    # Create simple coding agent with tracing
    agent = Agent(
        "coding_assistant",
        personality="a helpful coding assistant",
        tone="concise and practical",
        tools=[Shell, Files, Code]
    )
    
    # Simple coding workflow demo
    await agent.query("""Create a python file that calculates Fibonacci and execute it to verify correctness.""")

if __name__ == "__main__":
    asyncio.run(main())