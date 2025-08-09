"""Evaluation runner with auto-discovery."""

import asyncio
import importlib
import logging
import sys
from pathlib import Path

from .eval import Eval, report, run_suite

# Setup clean logging
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Silence noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def discover_evals() -> dict[str, type[Eval]]:
    """Auto-discover eval classes from suite/ directory."""
    evals = {}
    suite_dir = Path(__file__).parent / "suite"

    if not suite_dir.exists():
        return evals

    for py_file in suite_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = f"evals.suite.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find Eval subclasses
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Eval) and attr != Eval:
                    evals[attr.name] = attr

        except Exception as e:
            logger.warning(f"Failed to import {module_name}: {e}")

    return evals


async def main():
    """Run evals."""
    all_evals = discover_evals()
    if not all_evals:
        print("No evals found")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python -m evals.main [eval_name|all]")
        print(f"Available: {', '.join(sorted(all_evals.keys()))}")
        sys.exit(1)

    target = sys.argv[1].lower()
    if target == "all":
        eval_classes = list(all_evals.values())
    elif target in all_evals:
        eval_classes = [all_evals[target]]
    else:
        print(f"Unknown eval: {target}")
        print(f"Available: {', '.join(sorted(all_evals.keys()))}, all")
        sys.exit(1)

    print(f"🧠 Running {target} eval suite ({len(eval_classes)} evals)\n")

    results = await run_suite(eval_classes, sequential=True)
    print(report(results))
    sys.exit(0 if results["passed"] == results["total"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
