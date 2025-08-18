"""Core evaluation logic - category runner."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Callable
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG
from judge import judge

TestGenerator = Callable[[int], List[Dict[str, Any]]]


async def evaluate_category(category: str, generator: TestGenerator) -> Dict:
    """Run evaluation category with configurable judging."""
    agent = CONFIG.agent_provider()
    tests = generator(CONFIG.sample_size)
    results = []
    
    for i, test in enumerate(tests):
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
                **test
            }
            
            # Optional LLM judging
            if CONFIG.use_llm_judge:
                passed, judge_metadata = await judge(test["criteria"], prompt_used, response, CONFIG.judge_llm)
                result_data.update({"passed": passed, **judge_metadata})
            
            results.append(result_data)
            
        except Exception as e:
            results.append({
                "test_id": f"{category}_{i:02d}", 
                "error": str(e), 
                "passed": False if CONFIG.use_llm_judge else None
            })
    
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
        "results": results
    }