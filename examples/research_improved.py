#!/usr/bin/env python3
"""Multi-Tool Coordination - Enhanced Research Demo"""
import asyncio
from cogency import Agent
from cogency.utils.terminal import demo_header, stream_response, section, showcase, separator

async def main():
    demo_header("🔍 Cogency Advanced Research Demo", 40)
    
    # Create research agent with focused tool subset
    from cogency.tools import Search, Scrape, Files, Calculator, HTTP
    agent = Agent("research_assistant",
        identity="""expert research analyst who excels at finding, synthesizing, and presenting information.
        You're thorough, methodical, and skilled at evaluating conflicting information.
        You always cite your sources and explain your reasoning.""",
        tools=[Search(), Scrape(), Files(), Calculator(), HTTP()]  # Enhanced research toolkit
    )
    
    section("Complex Research Challenge")
    query = """I need a comprehensive analysis on the environmental impact of electric vehicles vs. traditional vehicles:
    
    1. Find recent (2023-2024) data comparing the lifetime carbon footprint of electric vs. gas vehicles
    2. Identify at least two conflicting viewpoints from reputable sources on this topic
    3. Analyze the manufacturing emissions for both vehicle types
    4. Calculate the break-even point in miles/kilometers where an EV becomes environmentally advantageous
    5. Save your findings to a file called 'ev_environmental_analysis.md' in markdown format
    
    Present a balanced analysis that acknowledges the complexity of the issue and cites all sources.
    """
    
    await stream_response(agent.stream(query))
    
    separator()
    showcase("🎯 This demo showcases:", [
        "Complex information synthesis",
        "Handling conflicting information",
        "Critical evaluation of sources",
        "Multi-perspective analysis",
        "Numerical reasoning with real-world data",
        "Structured report generation"
    ])

if __name__ == "__main__":
    asyncio.run(main())