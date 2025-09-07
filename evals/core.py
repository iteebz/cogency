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

    print(f"🧪 Test {i+1}: {test.get('complexity', 'unknown')}")

    agent = CONFIG.agent()

    try:
        import time

        user_id = f"eval_{category}_{i:02d}_{int(time.time())}"

        if "store_prompt" in test:
            # Simple memory test with agent destruction
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

        elif "evolution_prompts" in test:
            # Context evolution test - multiple interactions
            for prompt in test["evolution_prompts"]:
                await asyncio.wait_for(agent(prompt, user_id=user_id), timeout=CONFIG.timeout)

            # Agent destruction to test persistence
            del agent
            import gc

            gc.collect()
            agent = CONFIG.agent()

            response = await asyncio.wait_for(
                agent(test["final_prompt"], user_id=user_id), timeout=CONFIG.timeout
            )
            prompt_used = test["final_prompt"]

        elif "context_prompts" in test:
            # Complex synthesis test
            for prompt in test["context_prompts"]:
                await asyncio.wait_for(agent(prompt, user_id=user_id), timeout=CONFIG.timeout)

            del agent
            import gc

            gc.collect()
            agent = CONFIG.agent()

            response = await asyncio.wait_for(
                agent(test["synthesis_prompt"], user_id=user_id), timeout=CONFIG.timeout
            )
            prompt_used = test["synthesis_prompt"]

        elif test.get("test_type") == "mode_comparison":
            # Resume vs Replay performance test
            import time

            # Test resume mode (default)
            start_time = time.time()
            resume_agent = CONFIG.agent()  # Uses mode="auto" -> resume
            await asyncio.wait_for(
                resume_agent(test["prompt"], user_id=user_id), timeout=CONFIG.timeout
            )
            resume_time = time.time() - start_time

            # Test replay mode
            start_time = time.time()
            replay_agent = CONFIG.agent(mode="replay")
            await asyncio.wait_for(
                replay_agent(test["prompt"], user_id=f"{user_id}_replay"), timeout=CONFIG.timeout
            )
            replay_time = time.time() - start_time

            # Calculate performance metrics
            speedup = replay_time / resume_time if resume_time > 0 else 1.0

            response = (
                f"Resume: {resume_time:.2f}s | Replay: {replay_time:.2f}s | Speedup: {speedup:.1f}x"
            )
            prompt_used = test["prompt"]

            # Add performance data to result
            test["resume_time"] = resume_time
            test["replay_time"] = replay_time
            test["speedup"] = speedup

        else:
            # Standard test
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
        result_data = {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "response": response,
            "criteria": test["criteria"],
            "timestamp": datetime.now().isoformat(),
            "tool_traces": tool_traces,
            "reasoning_steps": reasoning_steps,
        }

        # Add all test fields including performance metrics
        result_data.update(test)

        return result_data

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


async def _simple_judge(result):
    """Simple LLM judge - no agent ceremony."""
    from cogency.lib.llms import Anthropic, OpenAI

    prompt = f"""Evaluate this test result:

CRITERIA: {result['criteria']}
PROMPT: {result['prompt']}
RESPONSE: {result['response']}
TOOL_TRACES: {result.get('tool_traces', [])}

Did the agent meet the evaluation criteria? Answer PASS or FAIL with brief reason.

Format: PASS: reason | FAIL: reason"""

    try:
        # Create judge LLM
        if CONFIG.judge_llm == "openai":
            judge = OpenAI()
        elif CONFIG.judge_llm == "anthropic":
            judge = Anthropic()
        else:
            return {"passed": False, "judge_reason": f"Unknown judge LLM: {CONFIG.judge_llm}"}

        # Make simple LLM call
        messages = [{"role": "user", "content": prompt}]
        result_obj = await judge.generate(messages)

        if not result_obj.success:
            return {"passed": False, "judge_reason": f"LLM error: {result_obj.error}"}

        response = result_obj.unwrap()

        # Parse PASS/FAIL from response
        if response.strip().upper().startswith("PASS"):
            return {"passed": True, "judge_reason": response.strip()}
        if response.strip().upper().startswith("FAIL"):
            return {"passed": False, "judge_reason": response.strip()}
        return {"passed": False, "judge_reason": f"Invalid judge response: {response}"}

    except Exception as e:
        return {"passed": False, "judge_reason": f"Judge error: {str(e)}"}
