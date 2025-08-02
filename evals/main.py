"""Beautiful eval runner - single entry point for all cogency evaluations."""

import asyncio
import sys

from .core import run_suite, save_report
from .tasks.coding.tool_usage import ToolUsage
from .tasks.custom.memory_persistence import MemoryPersistence
from .tasks.performance.tool_performance import ToolPerformance
from .tasks.reasoning.comprehension import Comprehension

# Import all eval classes
from .tasks.reasoning.math import MathReasoning

# Beautiful eval suites
QUICK_SUITE = [
    MathReasoning,
    ToolUsage,
]

REASONING_SUITE = [
    MathReasoning,
    Comprehension,
]

FULL_SUITE = [
    MathReasoning,
    Comprehension,
    ToolUsage,
    MemoryPersistence,
    ToolPerformance,
]

PERFORMANCE_SUITE = [
    ToolPerformance,
]


async def main():
    """Run the specified eval suite."""
    if len(sys.argv) < 2:
        print("Usage: python -m evals.main [quick|reasoning|full] [--sequential]")
        sys.exit(1)

    suite_name = sys.argv[1].lower()
    sequential = "--sequential" in sys.argv

    if suite_name == "quick":
        suite = QUICK_SUITE
    elif suite_name == "reasoning":
        suite = REASONING_SUITE
    elif suite_name == "full":
        suite = FULL_SUITE
    elif suite_name == "performance":
        suite = PERFORMANCE_SUITE
    else:
        print(f"Unknown suite: {suite_name}")
        print("Available suites: quick, reasoning, full, performance")
        print("Use --sequential for rate-limited environments")
        sys.exit(1)

    mode = "sequential" if sequential else "parallel"
    print(f"🧠 Running {suite_name} eval suite ({len(suite)} evals, {mode} mode)")
    print()

    # Run the suite
    report = await run_suite(suite, sequential=sequential)

    # Save report
    await save_report(report, suite_name)

    # Beautiful console output
    print(report.console())

    # Exit with appropriate code
    sys.exit(0 if report.passed == report.total else 1)


if __name__ == "__main__":
    asyncio.run(main())
