"""Run eval suites - beautiful execution of cogency evaluations."""

import asyncio
import sys

from suite import COGENCY_SUITE, PROVIDER_SUITE, QUICK_SUITE

from evals.core.runner import run_suite


async def main():
    """Run the specified eval suite."""
    if len(sys.argv) < 2:
        print("Usage: python -m evals.core.run_suite [quick|provider|full]")
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

    print(f"🧠 Running {suite_name} eval suite ({len(suite)} evals)")
    print()

    # Run the suite (uses .cogency/evals/ by default)
    report = await run_suite(suite)

    # Beautiful console output
    print(report.console())


if __name__ == "__main__":
    asyncio.run(main())
