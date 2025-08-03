"""Evaluation runner."""

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
from .tasks.security.context_overflow import ContextOverflow
from .tasks.security.direct_injection import DirectPromptInjection
from .tasks.security.indirect_injection import IndirectPromptInjection
from .tasks.security.shell_injection import ShellCommandInjection
from .tasks.tools.chains import ToolChains
from .tasks.tools.edges import ToolEdges

# Setup clean eval logging - suppress noise, force immediate output
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Silence noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# v1.0 Fast Suite - AGI lab gold standard for rapid validation
# Security-first + core capabilities. All evals use "fast" mode, complete <30s
FAST_SUITE = [
    # P0 Security gates (non-negotiable for deployment)
    DirectPromptInjection,  # declarative: command injection resistance
    ShellCommandInjection,  # declarative: tool args sanitization
    # Core reasoning foundation
    Comprehension,  # declarative: text analysis and logical inference
    # Tool integration core capability
    ToolUsage,  # declarative: discrete tool invocation patterns
    ToolPerformance,  # declarative: local tool latency microbenchmarks
]

# Security-focused suite for isolation testing
SECURITY_SUITE = [
    DirectPromptInjection,
    ShellCommandInjection,
    IndirectPromptInjection,
    ContextOverflow,
]

# v1.0 Production Suite - Complete 15-eval validation
# NOTE: Some evals use declarative test_cases pattern (discrete inputs),
# others remain procedural (complex integration scenarios)
FULL_SUITE = [
    # Core reasoning (2) - declarative
    MathReasoning,
    Comprehension,
    # Tool integration (4) - mixed: declarative + procedural
    ToolUsage,  # declarative: discrete tool tests
    ToolChains,  # procedural: workflow sequences
    ToolEdges,  # procedural: boundary conditions
    ToolPerformance,  # declarative: performance benchmarks
    # Agent orchestration (2) - mixed
    AgentConcurrency,  # procedural: concurrency scenarios
    MemoryPersistence,  # declarative: store/recall operations
    # Production resilience (3) - procedural
    NetworkResilience,  # procedural: failure handling
    ErrorRecovery,  # procedural: recovery workflows
    ComplexWorkflows,  # procedural: debugging scenarios
    # Security validation (4) - P0 for production
    DirectPromptInjection,  # declarative: command injection resistance
    IndirectPromptInjection,  # procedural: malicious content handling
    ShellCommandInjection,  # declarative: tool args sanitization
    ContextOverflow,  # procedural: resource boundary testing
]


async def main():
    """Run the specified eval suite."""
    if len(sys.argv) < 2:
        logger.error("Usage: python -m evals.main [fast|full|security|single] [--sequential] [--robust]")
        sys.exit(1)

    suite_name = sys.argv[1].lower()
    sequential = "--sequential" in sys.argv
    robust = "--robust" in sys.argv

    if suite_name == "fast":
        suite = FAST_SUITE
    elif suite_name == "full":
        suite = FULL_SUITE
    elif suite_name == "security":
        suite = SECURITY_SUITE
    elif suite_name == "single":
        # Single eval runner for debugging
        if len(sys.argv) < 3:
            logger.error("Usage: python -m evals.main single <eval_name>")
            logger.error("Available: direct_prompt_injection, shell_command_injection")
            sys.exit(1)
        eval_name = sys.argv[2]
        eval_map = {
            "direct_prompt_injection": DirectPromptInjection,
            "shell_command_injection": ShellCommandInjection,
        }
        if eval_name not in eval_map:
            logger.error(f"Unknown eval: {eval_name}")
            logger.error(f"Available: {', '.join(eval_map.keys())}")
            sys.exit(1)
        suite = [eval_map[eval_name]]
    else:
        logger.error(f"Unknown suite: {suite_name}")
        logger.error("Available suites: fast, full, security, single")
        logger.error("Use --sequential for rate-limited environments, --robust for retry logic")
        sys.exit(1)

    mode = "sequential" if sequential else "parallel"
    logger.info(f"🧠 Running {suite_name} eval suite ({len(suite)} evals, {mode} mode)")
    logger.info("")

    # Run the suite
    report = await run_suite(suite, sequential=sequential, robust=robust)

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
