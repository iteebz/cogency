#!/usr/bin/env python3
"""Multi-tool workflow: Calculate + verify pattern."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Code


async def main():
    print("🧮➡️🚀 MATH VERIFICATION WORKFLOW")
    print("=" * 40 + "\n")

    # Agent with calculator and code execution for verification
    agent = Agent(
        "math_verifier"
        identity="mathematical assistant who calculates quickly then verifies with code"
        tools=[Calculator(), Code()]
        memory=False
        depth=8,  # Allow for multi-step workflow
        trace=True
    )

    # Complex calculation that benefits from verification
    query = """I need to solve this compound interest problem:

    If I invest $5000 at 7% annual interest compounded quarterly for 3 years, 
    what will be the final amount?

    Use the formula: A = P(1 + r/n)^(nt)
    Where: P = principal, r = annual rate, n = compounds per year, t = time

    First calculate it step by step, then verify with code execution."""

    print("🎯 WORKFLOW QUERY:")
    print(f"{query}\n")
    print("=" * 40)

    try:
        result = await agent.run(query)
        print(f"\n✅ WORKFLOW RESULT:\n{result}")
    except Exception as e:
        print(f"\n❌ WORKFLOW ERROR: {e}")

    print("\n" + "=" * 40)
    print("🎵 Expected workflow:")
    print("  1. Parse the compound interest problem")
    print("  2. Use calculator for step-by-step computation")
    print("  3. Use code execution to verify the result")
    print("  4. Present both calculation and verification")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
