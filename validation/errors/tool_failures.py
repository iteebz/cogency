#!/usr/bin/env python3
"""Error handling verification - tool failures and recovery."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Code, Weather


async def main():
    print("❌➡️✅ ERROR HANDLING VERIFICATION")
    print("=" * 40 + "\n")

    # Agent with tools that might fail
    agent = Agent(
        "error_handler",
        identity="resilient assistant who handles errors gracefully",
        tools=[Calculator(), Code(), Weather()],
        memory=False,
        max_iterations=6,
        trace=False,
    )

    # Test cases that should trigger different types of errors
    error_scenarios = [
        {
            "name": "Division by Zero",
            "query": "Calculate 10 divided by 0",
            "expected": "Should handle division by zero gracefully",
        },
        {
            "name": "Invalid Code Syntax",
            "query": "Run this Python code: print('hello' +",
            "expected": "Should report syntax error clearly",
        },
        {
            "name": "Invalid City Name",
            "query": "What's the weather in XYZ123NOTACITY?",
            "expected": "Should handle city not found error",
        },
        {
            "name": "Complex Invalid Expression",
            "query": "Calculate: eval('import os; os.system(\"echo hack\")')",
            "expected": "Should reject unsafe expressions",
        },
    ]

    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"ERROR SCENARIO {i}: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print(f"Expected: {scenario['expected']}")
        print("─" * 40)

        try:
            result = await agent.run(scenario["query"])
            print(f"✅ GRACEFUL RESULT: {result}")
        except Exception as e:
            print(f"⚠️ EXCEPTION (might be ok): {e}")

        await asyncio.sleep(1)

    print(f"\n{'=' * 40}")
    print("✅ ERROR HANDLING VERIFICATION COMPLETE!")
    print("\nKey observations:")
    print("  • Errors should be handled gracefully")
    print("  • Agent should continue functioning after errors")
    print("  • Security: unsafe operations should be rejected")
    print("  • User gets helpful error messages, not crashes")
    print(f"{'=' * 40}")


if __name__ == "__main__":
    asyncio.run(main())
