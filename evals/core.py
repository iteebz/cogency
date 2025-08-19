"""Core evaluation logic - category runner."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG
from judge import judge
from sampling import stratify_by_difficulty

TestGenerator = Callable[[int], list[dict[str, Any]]]


async def evaluate_category(category: str, generator: TestGenerator) -> dict:
    """Run evaluation category with configurable judging."""
    # Generate larger pool for stratified sampling
    pool_size = CONFIG.sample_size * 2 if CONFIG.stratified_sampling else CONFIG.sample_size
    test_pool = generator(pool_size)

    # Apply stratified sampling if enabled
    if CONFIG.stratified_sampling and len(test_pool) > CONFIG.sample_size:
        tests = stratify_by_difficulty(test_pool, CONFIG.sample_size)
    else:
        tests = test_pool[: CONFIG.sample_size]

    results = []

    for i, test in enumerate(tests):
        # Fresh agent per test to prevent contamination
        agent = CONFIG.agent()
        try:
            if "store_prompt" in test:
                # Use consistent user_id for store/recall pair
                user_id = f"eval_{category}_{i:02d}"
                await agent(test["store_prompt"], user_id=user_id)
                agent_result = await agent(test["recall_prompt"], user_id=user_id)
                response = agent_result.response
                prompt_used = test["recall_prompt"]
            else:
                agent_result = await agent(test["prompt"])
                response = agent_result.response
                prompt_used = test["prompt"]

            # Capture full context for manual review
            result_data = {
                "test_id": f"{category}_{i:02d}",
                "prompt": prompt_used,
                "response": response,
                "criteria": test["criteria"],
                "timestamp": datetime.now().isoformat(),
                **test,
            }

            # Optional LLM judging
            if CONFIG.use_llm_judge:
                passed, judge_metadata = await judge(
                    test["criteria"], prompt_used, response, CONFIG.judge_llm
                )
                result_data.update({"passed": passed, **judge_metadata})

            results.append(result_data)

        except Exception as e:
            results.append(
                {
                    "test_id": f"{category}_{i:02d}",
                    "error": str(e),
                    "passed": False if CONFIG.use_llm_judge else None,
                }
            )

    # Calculate pass rate only if using LLM judge
    if CONFIG.use_llm_judge:
        passed_count = sum(1 for r in results if r.get("passed", False))
        pass_rate = passed_count / len(results) if results else 0
    else:
        passed_count = None
        pass_rate = None

    return {
        "category": category,
        "passed": passed_count,
        "total": len(results),
        "rate": pass_rate,
        "results": results,
    }
