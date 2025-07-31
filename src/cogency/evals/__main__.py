"""CLI for running evals: python -m cogency.evals <eval_name>"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Type

from .base import Eval
from .runner import run_eval, run_suite


def discover_evals() -> Dict[str, Type[Eval]]:
    """Discover all eval classes in evals/ directory."""
    evals = {}
    evals_dir = Path.cwd() / "evals"

    if not evals_dir.exists():
        return evals

    sys.path.insert(0, str(evals_dir.parent))

    for py_file in evals_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = f"evals.{py_file.stem}"
        try:
            module = __import__(module_name, fromlist=[""])
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Eval) and attr != Eval:
                    evals[attr.name] = attr
        except Exception:
            continue

    return evals


async def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m cogency.evals <eval_name|all>")
        print("       python -m cogency.evals list")
        sys.exit(1)

    command = sys.argv[1]
    evals = discover_evals()
    output_dir = Path.cwd() / "evals" / "reports"

    if command == "list":
        if not evals:
            print("X No evals found in evals/")
        else:
            print("Available evals:")
            for name in sorted(evals.keys()):
                print(f"  - {name}")
        return

    if command == "all":
        if not evals:
            print("X No evals found")
            return

        print(f"Running {len(evals)} evals...")
        report = await run_suite(list(evals.values()), output_dir)
        print(report.console())
        return

    if command not in evals:
        print(f"X Eval '{command}' not found")
        print(f"Available: {', '.join(sorted(evals.keys()))}")
        sys.exit(1)

    print(f"Running eval: {command}")
    report = await run_eval(evals[command], output_dir)
    print(report.console())


if __name__ == "__main__":
    asyncio.run(main())
