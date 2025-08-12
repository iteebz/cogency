#!/usr/bin/env python3
"""Intelligence Analyst - Deep research that connects the dots."""

import asyncio

from cogency import Agent, research_tools


async def main():
    print("🔍 INTELLIGENCE ANALYST")
    print("=" * 40)

    analyst = Agent("intelligence_analyst", tools=research_tools(), max_iterations=15)

    # Multi-source analysis with strategic insights
    response = await analyst.run_async("""
    Analyze the AI coding assistant market landscape:

    - Research major players (GitHub Copilot, Cursor, Claude, etc.)
    - Compare technical approaches and capabilities
    - Identify market gaps and opportunities
    - Assess competitive positioning for a new entrant
    - Recommend go-to-market strategy

    Provide strategic insights backed by data.
    """)

    print(response)


if __name__ == "__main__":
    asyncio.run(main())
