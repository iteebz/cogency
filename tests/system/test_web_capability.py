"""System Test: Web Capability Validation

Tests Search and Scrape tools working with Agent orchestration.
Validates real web integration without mocking web services.
"""

import asyncio

from cogency import Agent
from cogency.tools import Scrape, Search


async def main():
    print("🌐 TESTING WEB CAPABILITY INTEGRATION")
    print("=" * 50)

    # Agent with web tools
    web_tools = [Search(max_results=3), Scrape()]
    agent = Agent(tools=web_tools, max_iterations=3)

    # Test 1: Search capability
    print("\n🔍 Test 1: Search Integration")
    print("-" * 30)

    try:
        result = await agent(
            "Search for 'Python asyncio tutorial' and tell me about the first result"
        )
        print("✅ Search integration: SUCCESS")
        print(f"Response length: {len(result.response)} chars")
        print(f"Response preview: {result.response[:150]}...")

        # Check for search indicators
        if "search" in result.response.lower() or "found" in result.response.lower():
            print("✅ Search functionality: ACTIVE")
        else:
            print("⚠️  Search functionality: UNCLEAR")

    except Exception as e:
        print(f"❌ Search integration: FAILED - {e}")

    # Test 2: Scrape capability
    print("\n📄 Test 2: Scrape Integration")
    print("-" * 30)

    try:
        result = await agent(
            "Scrape the content from https://httpbin.org/html and summarize what you find"
        )
        print("✅ Scrape integration: SUCCESS")
        print(f"Response length: {len(result.response)} chars")
        print(f"Response preview: {result.response[:150]}...")

        # Check for scraping indicators
        if "content" in result.response.lower() or "page" in result.response.lower():
            print("✅ Scrape functionality: ACTIVE")
        else:
            print("⚠️  Scrape functionality: UNCLEAR")

    except Exception as e:
        print(f"❌ Scrape integration: FAILED - {e}")

    # Test 3: Combined workflow
    print("\n🔄 Test 3: Combined Web Workflow")
    print("-" * 35)

    try:
        result = await agent(
            "Search for 'Python official documentation' and then scrape content from the first result to tell me about Python"
        )
        print("✅ Combined workflow: SUCCESS")
        print(f"Response length: {len(result.response)} chars")
        print(f"Conversation: {result.conversation_id}")
        print(f"Response preview: {result.response[:200]}...")

        # Check for combined workflow indicators
        search_used = "search" in result.response.lower()
        scrape_used = "content" in result.response.lower() or "scraped" in result.response.lower()

        if search_used and scrape_used:
            print("✅ Combined workflow: FULLY INTEGRATED")
        elif search_used or scrape_used:
            print("✅ Combined workflow: PARTIALLY ACTIVE")
        else:
            print("⚠️  Combined workflow: UNCLEAR")

    except Exception as e:
        print(f"❌ Combined workflow: FAILED - {e}")

    print("\n🎯 WEB CAPABILITY VALIDATION COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
