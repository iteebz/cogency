"""Canonical evaluation runner - module interface + CLI."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import CONFIG
from .core import evaluate_category
from .generate import memory, reasoning, security, streaming


async def run(category=None, samples=None):
    """Run evaluation category or full suite."""
    samples = samples or CONFIG.sample_size

    if category == "reasoning":
        return await _run_category("reasoning", reasoning, samples)
    if category == "memory":
        return await _run_category("memory", memory, samples)
    if category == "streaming":
        return await _run_category("streaming", streaming, samples)
    if category == "security":
        return await _run_category("security", security, samples)
    return await _run_all(samples)


async def _run_category(name, generator, samples):
    """Execute single category evaluation."""
    print(f"🧠 {name.capitalize()} Evaluation")
    print("=" * 40)

    # Override config temporarily
    original_size = CONFIG.sample_size
    CONFIG.sample_size = samples

    try:
        result = await evaluate_category(name, generator)

        # Save to predictable location
        output_dir = Path.home() / ".cogency/evals"
        output_dir.mkdir(parents=True, exist_ok=True)

        category_file = output_dir / f"{name}.json"
        with open(category_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Results: {result.get('passed', 0)}/{result['total']}")
        print(f"Saved: {category_file}")

        return result

    finally:
        CONFIG.sample_size = original_size


async def _run_all(samples):
    """Execute full evaluation suite."""
    print("🧠 Cogency Evaluation Suite v3.0.0")
    print("=" * 50)

    categories = {
        "reasoning": reasoning,
        "memory": memory,
        "streaming": streaming,
        "security": security,
    }

    # Override config temporarily
    original_size = CONFIG.sample_size
    CONFIG.sample_size = samples

    try:
        results = await asyncio.gather(
            *[evaluate_category(name, generator) for name, generator in categories.items()]
        )

        # Calculate summary
        total = sum(r["total"] for r in results)
        passed = sum(r.get("passed", 0) for r in results if r.get("passed") is not None)
        rate = passed / total if total else 0

        summary = {
            "version": "v3.0.0",
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "rate": f"{rate:.1%}",
            "categories": {r["category"]: r for r in results},
        }

        # Save to predictable locations
        output_dir = Path.home() / ".cogency/evals"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Latest summary for Claude Code
        latest_file = output_dir / "latest.json"
        with open(latest_file, "w") as f:
            json.dump(summary, f, indent=2)

        # Individual category files
        for result in results:
            category_file = output_dir / f"{result['category']}.json"
            with open(category_file, "w") as f:
                json.dump(result, f, indent=2)

        print(f"Overall: {summary['rate']}")
        for result in results:
            rate = f"{result.get('rate', 0):.1%}" if result.get("rate") else "Raw"
            print(f"{result['category'].capitalize()}: {rate}")
        print(f"Latest: {latest_file}")

        return summary

    finally:
        CONFIG.sample_size = original_size


def latest():
    """Get latest evaluation summary."""
    latest_file = Path.home() / ".cogency/evals/latest.json"
    if latest_file.exists():
        with open(latest_file) as f:
            return json.load(f)
    return None


def logs(test_id):
    """Get debug logs for specific test."""
    # TODO: Implement test-specific log extraction
    return f"Debug logs for {test_id} - not yet implemented"


async def cli():
    """CLI entry point."""
    args = sys.argv[1:]

    samples = CONFIG.sample_size
    if "--samples" in args:
        idx = args.index("--samples")
        samples = int(args[idx + 1])
        args = [a for i, a in enumerate(args) if i not in [idx, idx + 1]]

    category = args[0] if args else None
    await run(category, samples)


if __name__ == "__main__":
    asyncio.run(cli())
