#!/usr/bin/env python3
"""Multi-Tool Coordination - Flagship ReAct Demo"""
import asyncio
from cogency import Agent

async def main():
    print("🔍 Cogency Research Demo")
    print("=" * 35)
    
    # Create research agent with focused tool subset
    from cogency.tools import Search, Scrape, Files, Calculator
    agent = Agent("research_assistant",
        personality="thorough research analyst",
        tone="analytical and comprehensive",
        tools=[Search(), Scrape(), Files(), Calculator()]  # Perfect research toolkit
    )
    
    print("\n=== Complex Research Query ===")
    query = """I need a comprehensive analysis of Python's current market position:
    
    1. Search for Python's popularity ranking among programming languages in 2024
    2. Scrape detailed content from the most relevant survey or report
    3. Calculate what percentage Python developers represent if there are 28 million total developers globally
    4. Get the current time and date for this research timestamp
    5. Save all findings to a file called 'python_market_analysis.txt'
    
    Provide a structured summary with sources and calculations.
    """
    
    await agent.query(query)
    
    print("\n" + "=" * 50)
    print("🎯 This demo showcases:")
    print("   • Multi-step reasoning")
    print("   • Intelligent tool selection") 
    print("   • Sequential tool dependencies")
    print("   • Web content extraction")
    print("   • Information synthesis")
    print("   • File output generation")

if __name__ == "__main__":
    asyncio.run(main())