#!/usr/bin/env python3
"""Multi-Tool Coordination - Flagship ReAct Demo"""
import asyncio
from cogency import Agent
from cogency.utils.terminal import demo_header, stream_response, section, showcase, separator

async def main():
    demo_header("🔍 Cogency Research Demo", 35)
    
    # Create research agent with focused tool subset
    from cogency.tools import Search, Scrape, Files, Calculator
    agent = Agent("research_assistant",
        identity="thorough research analyst",
        tools=[Search(), Scrape(), Files(), Calculator()]  # Perfect research toolkit
    )
    
    section("Complex Research Query")
    query = """I need a comprehensive analysis of Python's current market position:
    
    1. Search for Python's popularity ranking among programming languages in 2024
    2. Scrape detailed content from the most relevant survey or report
    3. Calculate what percentage Python developers represent if there are 28 million total developers globally
    4. Get the current time and date for this research timestamp
    5. Save all findings to a file called 'python_market_analysis.txt'
    
    Provide a structured summary with sources and calculations.
    """
    
    await stream_response(agent.stream(query))
    
    separator()
    showcase("🎯 This demo showcases:", [
        "Multi-step reasoning",
        "Intelligent tool selection",
        "Sequential tool dependencies", 
        "Web content extraction",
        "Information synthesis",
        "File output generation"
    ])

if __name__ == "__main__":
    asyncio.run(main())