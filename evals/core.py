"""Core evaluation logic - simplified from ceremony."""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from .config import CONFIG


async def evaluate_category(category: str, generator) -> dict:
    """Run evaluation category."""
    tests = generator(CONFIG.sample_size)

    # Parallel execution with semaphore to limit concurrency
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent tests

    async def run_test(i, test):
        async with semaphore:
            return await _execute_test(i, test, category)

    results = await asyncio.gather(
        *[run_test(i, test) for i, test in enumerate(tests)], return_exceptions=True
    )

    # Filter exceptions and add error handling
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append(
                {
                    "test_id": f"{category}_{i:02d}",
                    "error": str(result),
                    "passed": False,
                }
            )
        else:
            final_results.append(result)

    # Manual review - no LLM judge ceremony
    passed_count = len([r for r in final_results if not r.get("error")])

    return {
        "category": category,
        "passed": passed_count,
        "total": len(final_results),
        "rate": passed_count / len(final_results) if final_results else 0,
        "results": final_results,
    }


async def _execute_test(i, test, category):
    """Execute individual test with isolation."""
    # Clean sandbox between tests
    sandbox = Path(".sandbox")
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(exist_ok=True)

    print(f"🧪 Test {i+1}: {test.get('complexity', 'unknown')}")

    agent = CONFIG.agent()

    try:
        if "store_prompt" in test:
            # Memory test with agent destruction
            user_id = f"eval_{category}_{i:02d}"

            await asyncio.wait_for(
                agent(test["store_prompt"], user_id=user_id), timeout=CONFIG.timeout
            )

            if test.get("requires_agent_destruction"):
                del agent
                import gc

                gc.collect()
                agent = CONFIG.agent()

            response = await asyncio.wait_for(
                agent(test["recall_prompt"], user_id=user_id), timeout=CONFIG.timeout
            )
            prompt_used = test["recall_prompt"]
        else:
            # Standard test
            import time

            user_id = f"eval_{category}_{i:02d}_{int(time.time())}"

            result = await agent(test["prompt"], user_id=user_id)
            response = result.response if hasattr(result, "response") else str(result)
            prompt_used = test["prompt"]

        # Capture tool execution traces

        tool_traces = []
        reasoning_steps = []

        # Extract traces from stored conversation
        try:
            from cogency.lib.storage import load_messages

            conversation_id = f"{user_id}_session"  # Match agent's conversation_id pattern
            messages = load_messages(conversation_id)

            for msg in messages:
                if msg["type"] == "thinking":
                    reasoning_steps.append(msg["content"])
                elif msg["type"] == "calls":
                    tool_traces.append(msg["content"])
        except Exception:
            pass  # No traces available

        # Return enriched test result
        return {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "response": response,
            "criteria": test["criteria"],
            "timestamp": datetime.now().isoformat(),
            "tool_traces": tool_traces,
            "reasoning_steps": reasoning_steps,
            **test,
        }

    except asyncio.TimeoutError:
        return {
            "test_id": f"{category}_{i:02d}",
            "error": "Timeout",
            "passed": False,
        }
    except Exception as e:
        return {
            "test_id": f"{category}_{i:02d}",
            "error": str(e),
            "passed": False,
        }
