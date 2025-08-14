#!/usr/bin/env python3
"""Tool validation - direct tool testing for Claude debugging."""

import asyncio

from cogency.tools import Files, Scrape, Search, Shell


async def main():
    """Test all tools directly."""
    print("=== TOOL VALIDATION ===")

    tools = [Files(), Shell(), Search(), Scrape()]

    for tool in tools:
        print(f"\n{tool.name}: {tool.description}")
        print(f"Schema: {getattr(tool, 'schema', 'No schema')}")

        # Test basic functionality
        try:
            if tool.name == "files":
                result = await tool.run(action="list", path=".")
                print(f"✅ Files test: {result.success if hasattr(result, 'success') else 'OK'}")

            elif tool.name == "shell":
                result = await tool.run(command="echo test", timeout=5000)
                print(f"✅ Shell test: {result.success if hasattr(result, 'success') else 'OK'}")

            elif tool.name == "search":
                result = await tool.run(query="test", limit=1)
                print(f"✅ Search test: {result.success if hasattr(result, 'success') else 'OK'}")

            elif tool.name == "scrape":
                # Skip actual scraping to avoid network calls
                print("⏭️  Scrape test skipped (network)")

        except Exception as e:
            print(f"❌ {tool.name} error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
