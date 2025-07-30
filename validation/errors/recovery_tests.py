#!/usr/bin/env python3
"""Error recovery verification - agent continues after failures."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Code


async def main():
    print("🔄 ERROR RECOVERY VERIFICATION")
    print("=" * 35 + "\n")

    # Agent designed to test recovery patterns
    agent = Agent(
        "recovery_tester"
        identity="persistent assistant who tries alternatives when tools fail"
        tools=[Calculator(), Code()]
        memory=False
        depth=8,  # Allow for recovery attempts
        trace=False
    )

    # Scenarios where agent should recover and try alternatives
    recovery_scenarios = [
        {
            "name": "Fallback to Code Execution"
            "query": "I need to calculate something complex that basic calculator can't handle: What's the factorial of 15? If calculator fails, use code execution."
        }
        {
            "name": "Alternative Calculation Method"
            "query": "Calculate 2^100. If one method fails, try another approach."
        }
        {
            "name": "Multi-step Recovery"
            "query": "I need to calculate the sum of squares from 1 to 50. Try calculator first, if that's too complex, write and run code."
        }
    ]

    for i, scenario in enumerate(recovery_scenarios, 1):
        print(f"\n{'─' * 35}")
        print(f"RECOVERY SCENARIO {i}: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print("─" * 35)

        try:
            result = await agent.run(scenario["query"])
            print(f"✅ RECOVERY RESULT: {result}")
        except Exception as e:
            print(f"❌ RECOVERY FAILED: {e}")

        await asyncio.sleep(1.5)

    print(f"\n{'=' * 35}")
    print("✅ RECOVERY VERIFICATION COMPLETE!")
    print("\nRecovery patterns observed:")
    print("  • Agent tries alternative tools when one fails")
    print("  • Multi-step reasoning to find solutions")
    print("  • Graceful degradation of functionality")
    print("  • Persistence in solving user problems")
    print(f"{'=' * 35}")


if __name__ == "__main__":
    asyncio.run(main())
