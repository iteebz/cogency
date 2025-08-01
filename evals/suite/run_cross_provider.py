"""Cross-provider benchmarking - comparative performance analysis across LLM providers."""

import asyncio
import sys

from suite import COGENCY_SUITE, PROVIDER_SUITE, QUICK_SUITE

from evals.core.runner import run_suite_cross_provider


async def main():
    """Run cross-provider benchmarking for the specified eval suite."""
    if len(sys.argv) < 2:
        print("Usage: python run_cross_provider.py [quick|provider|full]")
        sys.exit(1)

    suite_name = sys.argv[1].lower()

    if suite_name == "quick":
        suite = QUICK_SUITE
    elif suite_name == "provider":
        suite = PROVIDER_SUITE
    elif suite_name == "full":
        suite = COGENCY_SUITE
    else:
        print(f"Unknown suite: {suite_name}")
        print("Available suites: quick, provider, full")
        sys.exit(1)

    print(f"🔥 Cross-Provider Benchmarking: {suite_name} suite ({len(suite)} evals)")
    print("Testing across all available LLM providers...")
    print()

    # Run cross-provider benchmarking
    await run_suite_cross_provider(suite)


if __name__ == "__main__":
    asyncio.run(main())
