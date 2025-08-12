#!/usr/bin/env python3
"""Tool Composition - Mix and match capabilities."""

import asyncio

from cogency import Agent, analysis_tools, devops_tools, research_tools, web_tools
from cogency.tools import Tool, tool


@tool
class DatabaseTool(Tool):
    """Custom database tool for specialized queries."""

    def __init__(self):
        super().__init__("database", "Execute database queries and analysis")

    async def run(self, query: str):
        # Simulate database operation
        return {
            "query": query,
            "result": "Database query executed successfully",
            "rows_affected": 42,
        }


async def main():
    print("TOOL COMPOSITION EXAMPLES")
    print("=" * 50)

    # DevOps agent - Files + Shell + Search
    print("\n1. DevOps Agent (Files + Shell + Search)")
    devops = Agent("devops", tools=devops_tools())
    await devops.run_async("Check system disk usage and suggest cleanup")

    # Research agent - Search + Scrape + Retrieve
    print("\n2. Research Agent (Search + Scrape + Retrieve)")
    researcher = Agent("researcher", tools=research_tools())
    await researcher.run_async("Find latest trends in AI agent frameworks")

    # Web agent - Search + Scrape
    print("\n3. Web Agent (Search + Scrape)")
    web = Agent("web", tools=web_tools())
    await web.run_async("What's the latest news about Python 3.13?")

    # Analysis agent - Files + Retrieve + Recall
    print("\n4. Analysis Agent (Files + Retrieve + Recall)")
    analyst = Agent("analyst", tools=analysis_tools(), memory=True)
    await analyst.run_async("Analyze the codebase structure and remember key patterns")

    # Custom composition - Mix built-in tools with custom ones
    print("\n5. Custom Composition (DevOps + Custom Database)")
    custom = Agent("custom", tools=devops_tools() + [DatabaseTool()])
    await custom.run_async("Check database performance and system resources")

    print("\nAll tool compositions working!")


if __name__ == "__main__":
    asyncio.run(main())
