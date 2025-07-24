#!/usr/bin/env python3
"""Coding agent - impressive multi-file project generation."""

import asyncio

from cogency import Agent
from cogency.utils.cli import trace_args
from cogency.tools import Code, Files, Shell


async def main():
    print("🚀 CODING AGENT")
    print("=" * 25 + "\n")

    # Create coding agent
    agent = Agent(
        "coder",
        identity="world-class software engineer who writes clean, production-ready code",
        tools=[Code(), Files(), Shell()],
        memory=False,
        max_iterations=20,
        trace=trace_args()
    )

    # Fun, impressive coding challenge
    query = """Create a complete Python web scraper and API dashboard:

    Build a multi-file project with:
    1. Web scraper that fetches trending GitHub repositories
    2. FastAPI backend with endpoints to serve the data
    3. Simple HTML dashboard to display trending repos
    4. Data models with proper validation
    5. Error handling and rate limiting
    6. Requirements.txt with all dependencies
    7. A simple test to verify it works

    Make it production-ready with clean structure, proper error handling, and documentation."""

    print(f"💻 Challenge: {query[:60]}...\n")

    # Stream the response
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
