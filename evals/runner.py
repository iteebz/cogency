"""Evaluation orchestration - baseline measurement."""

import asyncio
from datetime import datetime
from typing import Dict

from .core import evaluate_category, TestGenerator
from .config import CONFIG
from .storage import save_run


async def baseline_evaluation(categories: Dict[str, TestGenerator]) -> Dict:
    """Run baseline evaluation."""
    
    results = await asyncio.gather(*[
        evaluate_category(name, generator) 
        for name, generator in categories.items()
    ])
    
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
            "use_llm_judge": CONFIG.use_llm_judge
        },
        "categories": results,
        "summary": {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_rate": overall_rate,
            "breakdown": breakdown
        }
    }
    
    run_dir = save_run(evaluation)
    evaluation["run_path"] = str(run_dir)
    
    return evaluation