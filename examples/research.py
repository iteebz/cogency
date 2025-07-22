#!/usr/bin/env python3
"""Multi-Tool Coordination - Flagship ReAct Demo"""

import asyncio

from cogency import Agent
from cogency.utils import demo_header, trace_args, stream_response


async def main():
    demo_header("🔍 Cogency Research Demo")

    user = "👤 HUMAN: "
    researcher = "🔬 RESEARCHER: "

    # Create research agent with focused tool subset
    from cogency.tools import Calculator, Files, Scrape, Search

    agent = Agent(
        "research_assistant",
        identity="thorough research analyst",
        tools=[Search(), Scrape(), Files(), Calculator()],
        memory=False,
        trace=trace_args()
    )

    # Complex Research Query
    query = """
Research the current state of AGI/ASI development and provide a comprehensive analysis:

1. Search for recent developments in AGI research and timeline predictions (2024-2025)
2. Find information about current ASI (Artificial Superintelligence) theoretical frameworks
3. Research the "AI singularity" concept and expert predictions
4. Investigate both accelerationist and doomerist perspectives on AI development
5. Calculate investment trends if you can find funding data for AGI companies
6. Save comprehensive findings to 'agi_analysis_2025.txt'

Synthesize conflicting expert opinions and present a balanced analysis with sources.
This topic requires navigating contested claims, rapid developments, and diverse perspectives.
"""
    print(f"{user}{query}\n")
    await stream_response(agent.stream(query), prefix=researcher)


if __name__ == "__main__":
    asyncio.run(main())
