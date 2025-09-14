"""Core evaluation logic - simplified from ceremony."""

import asyncio
import shutil
from pathlib import Path

from .config import CONFIG


async def evaluate_category(category: str, generator) -> dict:
    """Run evaluation category."""
    # Apply seed for reproducible sampling
    import random

    random.seed(CONFIG.seed)

    tests = generator(CONFIG.sample_size)

    # Parallel execution with semaphore to limit concurrency
    semaphore = asyncio.Semaphore(CONFIG.max_concurrent_tests)

    async def run_test(i, test):
        async with semaphore:
            # Stagger requests to spread across rotated keys
            await asyncio.sleep(i * 0.2)  # 200ms delay per task
            return await _execute_test(i, test, category)

    results = await asyncio.gather(
        *[run_test(i, test) for i, test in enumerate(tests)], return_exceptions=True
    )

    # Filter exceptions
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append({"test_id": f"{category}_{i:02d}", "error": str(result), "passed": False})
        else:
            final_results.append(result)

    # Judge results - REQUIRED, no fake passing
    judged_results = []
    for result in final_results:
        if result.get("error"):
            result["passed"] = False
            judged_results.append(result)
        elif CONFIG.judge_llm:
            judgment = await _simple_judge(result)
            result.update(judgment)
            judged_results.append(result)
        else:
            # No judge = manual review required, no auto-pass
            result["passed"] = None  # Explicitly unknown
            result["judge_reason"] = "Manual review required - no judge configured"
            judged_results.append(result)

    # Count only explicitly passed tests
    passed_count = len([r for r in judged_results if r.get("passed") is True])

    return {
        "category": category,
        "passed": passed_count,
        "total": len(judged_results),
        "rate": passed_count / len(judged_results) if judged_results else 0,
        "results": judged_results,
    }


async def _execute_test(i, test, category):
    """Execute individual test with isolation."""
    # Clean sandbox between tests
    sandbox = Path(".sandbox")
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(exist_ok=True)

    print(f"🧪 Test {i + 1}: {test.get('complexity', 'unknown')}")

    agent = CONFIG.agent()

    try:
        import time

        user_id = f"eval_{category}_{i:02d}_{int(time.time())}"
        start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0

        if "store_prompt" in test:
            # Memory test with agent destruction
            store_stream = agent(test["store_prompt"], user_id=user_id)

            async for event in store_stream:
                if event["type"] == "metrics":
                    total = event["total"]
                    total_input_tokens = total["input"]
                    total_output_tokens = total["output"]

            if test.get("requires_agent_destruction"):
                del agent
                import gc
                gc.collect()
                agent = CONFIG.agent()

            recall_stream = agent(test["recall_prompt"], user_id=user_id)
            stream = []
            
            async for event in recall_stream:
                if event["type"] == "metrics":
                    total = event["total"]
                    total_input_tokens = total["input"]
                    total_output_tokens = total["output"]
                else:
                    # Convert to readable stream format
                    event_type = event["type"].upper()
                    content = str(event.get("content", ""))
                    stream.append(f"{event_type}: {content}")

            prompt_used = test["recall_prompt"]

        elif "evolution_prompts" in test:
            # Context evolution test - multiple interactions
            for prompt in test["evolution_prompts"]:
                evolution_stream = agent(prompt, user_id=user_id)

                async for event in evolution_stream:
                    if event["type"] == "metrics":
                        total = event["total"]
                        total_input_tokens = total["input"]
                        total_output_tokens = total["output"]

            # Agent destruction to test persistence
            del agent
            import gc
            gc.collect()
            agent = CONFIG.agent()

            final_stream = agent(test["final_prompt"], user_id=user_id)
            stream = []
            
            async for event in final_stream:
                if event["type"] == "metrics":
                    total = event["total"]
                    total_input_tokens = total["input"]
                    total_output_tokens = total["output"]
                else:
                    # Convert to readable stream format
                    event_type = event["type"].upper()
                    content = str(event.get("content", ""))
                    stream.append(f"{event_type}: {content}")

            prompt_used = test["final_prompt"]

        elif "context_prompts" in test:
            # Complex synthesis test
            for prompt in test["context_prompts"]:
                context_stream = agent(prompt, user_id=user_id)

                async for event in context_stream:
                    if event["type"] == "metrics":
                        total = event["total"]
                        total_input_tokens = total["input"]
                        total_output_tokens = total["output"]

            del agent
            import gc
            gc.collect()
            agent = CONFIG.agent()

            synthesis_stream = agent(test["synthesis_prompt"], user_id=user_id)
            stream = []
            
            async for event in synthesis_stream:
                if event["type"] == "metrics":
                    total = event["total"]
                    total_input_tokens = total["input"]
                    total_output_tokens = total["output"]
                else:
                    # Convert to readable stream format
                    event_type = event["type"].upper()
                    content = str(event.get("content", ""))
                    stream.append(f"{event_type}: {content}")

            prompt_used = test["synthesis_prompt"]

        else:
            # Standard test - capture all events except metrics
            stream_events = agent(test["prompt"], user_id=user_id)
            stream = []
            
            async for event in stream_events:
                if event["type"] == "metrics":
                    total = event["total"]
                    total_input_tokens = total["input"]
                    total_output_tokens = total["output"]
                else:
                    # Convert to readable stream format
                    event_type = event["type"].upper()
                    content = str(event.get("content", ""))
                    stream.append(f"{event_type}: {content}")

            prompt_used = test["prompt"]


        total_seconds = time.time() - start_time

        return {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "stream": stream,
            "tokens": [total_input_tokens, total_output_tokens],
            "seconds": round(total_seconds, 2),
            "criteria": test["criteria"],
        }

    except asyncio.TimeoutError:
        return {"test_id": f"{category}_{i:02d}", "error": "Timeout", "passed": False}
    except Exception as e:
        return {"test_id": f"{category}_{i:02d}", "error": str(e), "passed": False}


async def _simple_judge(result):
    """Simple LLM judge - no agent ceremony."""
    from cogency.lib.llms import Anthropic, Gemini, OpenAI

    # Stream is already formatted as strings
    stream_text = "\n".join(result.get("stream", []))

    prompt = f"""Evaluate this test result:

CRITERIA: {result["criteria"]}
PROMPT: {result["prompt"]}
AGENT_STREAM:
{stream_text}

Did the agent meet the evaluation criteria? Answer PASS or FAIL with brief reason.

Format: PASS: reason | FAIL: reason"""

    try:
        # Create judge LLM
        if CONFIG.judge_llm == "openai":
            judge = OpenAI()
        elif CONFIG.judge_llm == "anthropic":
            judge = Anthropic()
        elif CONFIG.judge_llm == "gemini":
            judge = Gemini()
        else:
            return {"passed": False, "judge_reason": f"Unknown judge LLM: {CONFIG.judge_llm}"}

        # Make simple LLM call - handle different message formats
        if CONFIG.judge_llm == "gemini":
            # Gemini expects simple string content, not role-based messages
            response = await judge.generate([prompt])
        else:
            # OpenAI/Anthropic expect structured messages
            messages = [{"role": "user", "content": prompt}]
            response = await judge.generate(messages)

        # Parse PASS/FAIL from response
        clean_response = response.strip().upper()
        if clean_response.startswith("PASS"):
            return {"passed": True, "judge_reason": response.strip()}
        elif clean_response.startswith("FAIL"):
            return {"passed": False, "judge_reason": response.strip()}
        else:
            return {"passed": False, "judge_reason": f"Invalid judge response: {response}"}

    except Exception as e:
        return {"passed": False, "judge_reason": f"Judge error: {str(e)}"}
