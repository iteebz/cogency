"""Evaluation orchestration - baseline measurement."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG
from core import TestGenerator, evaluate_category
from storage import save_run


async def run_category(category_name: str, generator: TestGenerator) -> dict:
    """Run evaluation for a single category."""
    print(f"🧠 Running {category_name.capitalize()} Evaluation")
    print("=" * 50)

    result = await evaluate_category(category_name, generator)

    # Create minimal run data for single category
    run_data = {
        "version": f"v2.1.0-{category_name}",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "sample_size": CONFIG.sample_size,
            "categories": [category_name],
            "use_llm_judge": CONFIG.use_llm_judge,
        },
        "categories": [result],
        "summary": {
            "overall_rate": f"{result['rate']:.1%}" if result["rate"] else "N/A (raw output)",
            "breakdown": {
                category_name: f"{result['rate']:.1%}" if result["rate"] else "Raw outputs saved"
            },
        },
    }

    run_path = save_run(run_data)

    print(f"\n{category_name.capitalize()} Results:")
    print(f"Passed: {result['passed']}/{result['total']}")
    print(f"Rate: {result['rate']:.1%}" if result["rate"] else "Rate: N/A (raw output)")
    print(f"Results saved to: {run_path}")

    return run_data


async def run_baseline(categories: dict[str, TestGenerator]) -> dict:
    """Run baseline evaluation."""

    results = await asyncio.gather(
        *[evaluate_category(name, generator) for name, generator in categories.items()]
    )

    total_tests = sum(r["total"] for r in results)

    # Handle None values from raw output mode
    if CONFIG.use_llm_judge:
        total_passed = sum(r["passed"] for r in results)
        overall_rate = total_passed / total_tests if total_tests else 0
        breakdown = {r["category"]: r["rate"] for r in results}
    else:
        total_passed = "N/A (raw output mode)"
        overall_rate = "N/A (raw output mode)"
        breakdown = {r["category"]: "Raw outputs saved" for r in results}

    evaluation = {
        "version": "v2.1.0-baseline",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "sample_size": CONFIG.sample_size,
            "categories": list(categories.keys()),
            "use_llm_judge": CONFIG.use_llm_judge,
        },
        "categories": results,
        "summary": {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_rate": overall_rate,
            "breakdown": breakdown,
        },
    }

    run_dir = save_run(evaluation)
    evaluation["run_path"] = str(run_dir)

    return evaluation
