"""Beautiful eval runner - single entry point for all cogency evaluations."""

import asyncio
import logging
import sys

from .core import run_suite, save_report
from .tasks.agents.concurrency import AgentConcurrency
from .tasks.coding.tool_usage import ToolUsage
from .tasks.custom.memory_persistence import MemoryPersistence
from .tasks.performance.tool_performance import ToolPerformance
from .tasks.reasoning.comprehension import Comprehension
from .tasks.reasoning.math import MathReasoning
from .tasks.resilience.network import NetworkResilience
from .tasks.resilience.recovery import ErrorRecovery
from .tasks.scenarios.workflows import ComplexWorkflows
from .tasks.tools.chains import ToolChains
from .tasks.tools.edges import ToolEdges

# Setup clean eval logging - suppress noise
logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Silence noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

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

# v1.0 Production Suite - Complete 11-eval validation
V1_SUITE = [
    # Core reasoning (2)
    MathReasoning,
    Comprehension,
    # Tool integration (4)
    ToolUsage,
    ToolChains,
    ToolEdges,
    ToolPerformance,
    # Agent orchestration (2)
    AgentConcurrency,
    MemoryPersistence,
    # Production resilience (3)
    NetworkResilience,
    ErrorRecovery,
    ComplexWorkflows,
]


async def main():
    """Run the specified eval suite."""
    if len(sys.argv) < 2:
        logger.error(
            "Usage: python -m evals.main [quick|reasoning|full|performance|v1] [--sequential]"
        )
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
    elif suite_name == "v1":
        suite = V1_SUITE
    else:
        logger.error(f"Unknown suite: {suite_name}")
        logger.error("Available suites: quick, reasoning, full, performance, v1")
        logger.error("Use --sequential for rate-limited environments")
        sys.exit(1)

    mode = "sequential" if sequential else "parallel"
    logger.info(f"🧠 Running {suite_name} eval suite ({len(suite)} evals, {mode} mode)")
    logger.info("")

    # Run the suite
    report = await run_suite(suite, sequential=sequential)

    # Save bundled report with all artifacts
    run_dir = await save_report(report, suite_name)

    # Beautiful console output
    logger.info(report.console())
    logger.info("")
    logger.info(f"📁 Full run artifacts saved: {run_dir}")

    # Exit with appropriate code
    sys.exit(0 if report.passed == report.total else 1)


if __name__ == "__main__":
    asyncio.run(main())
