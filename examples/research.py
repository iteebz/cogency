#!/usr/bin/env python3
"""Research agent - deep analysis with longer horizon planning."""

import asyncio

from cogency import Agent
from cogency.tools import Scrape, Search
from cogency.utils.cli import trace_args


async def main():
    print("🔍 DEEP RESEARCH AGENT")
    print("=" * 30 + "\n")

    # Research agent with longer horizon capabilities
    agent = Agent(
        "deep_researcher",
        identity="expert research analyst who conducts thorough multi-step research and analysis",
        tools=[Scrape(), Search()],
        memory=False,
        max_iterations=10,  # Allow deeper research with multiple steps
        trace=trace_args(),
    )

    # Complex research query that demonstrates longer horizon planning
    query = """Conduct comprehensive research on the current state of quantum computing:

    Please research and analyze:
    1. Latest quantum computing breakthroughs and milestones (2024-2025)
    2. Leading companies and their quantum systems (IBM, Google, Rigetti, etc.)
    3. Current practical applications and real-world use cases
    4. Technical challenges and limitations still being addressed
    5. Expert predictions on quantum advantage timeline
    6. Impact on cryptography and security implications
    
    Provide a structured analysis with sources and key findings from your research."""

    print(f"👤 {query[:80]}...\n")
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
