#!/usr/bin/env python3
"""Multi-Tool Coordination - Flagship ReAct Demo"""

import asyncio

from cogency import Agent
from cogency.utils import (
    demo_header,
    parse_trace_args,
    section,
    separator,
    showcase,
    stream_response,
)


async def main():
    demo_header("🔍 Cogency Research Demo", 35)

    # Create research agent with focused tool subset
    from cogency.tools import Calculator, Files, Scrape, Search

    agent = Agent(
        "research_assistant",
        identity="thorough research analyst",
        tools=[Search(), Scrape(), Files(), Calculator()],  # Perfect research toolkit
        trace=parse_trace_args(),
    )

    section("Complex Research Query")
    query = """Research the current state of AGI/ASI development and provide a comprehensive analysis:
    
    1. Search for recent developments in AGI research and timeline predictions (2024-2025)
    2. Find information about current ASI (Artificial Superintelligence) theoretical frameworks
    3. Research the "AI singularity" concept and expert predictions
    4. Investigate both accelerationist and doomerist perspectives on AI development
    5. Calculate investment trends if you can find funding data for AGI companies
    6. Save comprehensive findings to 'agi_analysis_2025.txt'
    
    Synthesize conflicting expert opinions and present a balanced analysis with sources.
    This topic requires navigating contested claims, rapid developments, and diverse perspectives.
    """

    await stream_response(agent.stream(query))

    separator()
    showcase(
        "🎯 This demo showcases:",
        [
            "Enhanced cognitive reasoning preventing plan fixation",
            "Adaptive strategy selection across contested domains",
            "Multi-source synthesis with conflicting expert opinions",
            "Loop detection preventing repetitive search patterns",
            "Context-aware information synthesis",
            "Complex research topic navigation",
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
