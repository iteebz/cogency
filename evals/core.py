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

    print(f"🧪 Test {i + 1}: {test.get('complexity', 'unknown')}")

    agent = CONFIG.agent()

    try:
        import time

        from cogency.lib.observer import Observer

        user_id = f"eval_{category}_{i:02d}_{int(time.time())}"

        # Metrics collection
        start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0

        if "store_prompt" in test:
            # Simple memory test with agent destruction
            store_stream = agent(test["store_prompt"], user_id=user_id)
            observer = Observer(store_stream, agent.config.llm.llm_model)

            async for _event in observer:
                pass  # Consume stream to get metrics

            metrics = observer.get_metrics()
            total_input_tokens += metrics["input_tokens"]
            total_output_tokens += metrics["output_tokens"]

            if test.get("requires_agent_destruction"):
                del agent
                import gc

                gc.collect()
                agent = CONFIG.agent()

            recall_stream = agent(test["recall_prompt"], user_id=user_id)
            observer = Observer(recall_stream, agent.config.llm.llm_model)

            response = ""
            async for event in observer:
                if event.get("type") == "respond":
                    response += event.get("content", "")

            metrics = observer.get_metrics()
            total_input_tokens += metrics["input_tokens"]
            total_output_tokens += metrics["output_tokens"]
            prompt_used = test["recall_prompt"]

        elif "evolution_prompts" in test:
            # Context evolution test - multiple interactions
            for prompt in test["evolution_prompts"]:
                stream = agent(prompt, user_id=user_id)
                observer = Observer(stream, agent.config.llm.llm_model)

                async for _event in observer:
                    pass  # Consume stream

                metrics = observer.get_metrics()
                total_input_tokens += metrics["input_tokens"]
                total_output_tokens += metrics["output_tokens"]

            # Agent destruction to test persistence
            del agent
            import gc

            gc.collect()
            agent = CONFIG.agent()

            final_stream = agent(test["final_prompt"], user_id=user_id)
            observer = Observer(final_stream, agent.config.llm.llm_model)

            response = ""
            async for event in observer:
                if event.get("type") == "respond":
                    response += event.get("content", "")

            metrics = observer.get_metrics()
            total_input_tokens += metrics["input_tokens"]
            total_output_tokens += metrics["output_tokens"]
            prompt_used = test["final_prompt"]

        elif "context_prompts" in test:
            # Complex synthesis test
            for prompt in test["context_prompts"]:
                stream = agent(prompt, user_id=user_id)
                observer = Observer(stream, agent.config.llm.llm_model)

                async for _event in observer:
                    pass  # Consume stream

                metrics = observer.get_metrics()
                total_input_tokens += metrics["input_tokens"]
                total_output_tokens += metrics["output_tokens"]

            del agent
            import gc

            gc.collect()
            agent = CONFIG.agent()

            synthesis_stream = agent(test["synthesis_prompt"], user_id=user_id)
            observer = Observer(synthesis_stream, agent.config.llm.llm_model)

            response = ""
            async for event in observer:
                if event.get("type") == "respond":
                    response += event.get("content", "")

            metrics = observer.get_metrics()
            total_input_tokens += metrics["input_tokens"]
            total_output_tokens += metrics["output_tokens"]
            prompt_used = test["synthesis_prompt"]

        elif test.get("test_type") == "mode_comparison":
            # Resume vs Replay performance test
            resume_start = time.time()
            resume_agent = CONFIG.agent()  # Uses mode="auto" -> resume

            resume_stream = resume_agent(test["prompt"], user_id=user_id)
            observer = Observer(resume_stream, resume_agent.config.llm.llm_model)

            async for _event in observer:
                pass  # Consume stream

            resume_metrics = observer.get_metrics()
            resume_time = time.time() - resume_start

            # Test replay mode
            replay_start = time.time()
            replay_agent = CONFIG.agent(mode="replay")

            replay_stream = replay_agent(test["prompt"], user_id=f"{user_id}_replay")
            observer = Observer(replay_stream, replay_agent.config.llm.llm_model)

            async for _event in observer:
                pass  # Consume stream

            replay_metrics = observer.get_metrics()
            replay_time = time.time() - replay_start

            # Aggregate token counts
            total_input_tokens = resume_metrics["input_tokens"] + replay_metrics["input_tokens"]
            total_output_tokens = resume_metrics["output_tokens"] + replay_metrics["output_tokens"]

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
            stream = agent(test["prompt"], user_id=user_id)
            observer = Observer(stream, agent.config.llm.llm_model)

            response = ""
            async for event in observer:
                if event.get("type") == "respond":
                    response += event.get("content", "")

            metrics = observer.get_metrics()
            total_input_tokens += metrics["input_tokens"]
            total_output_tokens += metrics["output_tokens"]
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

        # Build canonical stream format
        stream = []

        # Add reasoning steps as THINK events
        for step in reasoning_steps:
            stream.append({"type": "think", "content": step})

        # Add tool executions as CALLS events
        for trace in tool_traces:
            stream.append({"type": "calls", "content": trace})

        # Add response as final RESPOND event
        if response:
            stream.append({"type": "respond", "content": response})

        # Calculate final timing
        total_seconds = time.time() - start_time

        # Canonical result format - mirror architecture
        result_data = {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "stream": stream,
            "tokens": [total_input_tokens, total_output_tokens],
            "seconds": round(total_seconds, 2),
            "criteria": test["criteria"],
        }

        # Add performance metrics if available
        if "resume_time" in test:
            result_data["resume_time"] = test["resume_time"]
        if "replay_time" in test:
            result_data["replay_time"] = test["replay_time"]
        if "speedup" in test:
            result_data["speedup"] = test["speedup"]

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

    # Extract response from stream
    response = ""
    tool_traces = []
    for event in result.get("stream", []):
        if event.get("type") == "respond":
            response += event.get("content", "")
        elif event.get("type") == "calls":
            tool_traces.append(event.get("content", ""))

    prompt = f"""Evaluate this test result:

CRITERIA: {result["criteria"]}
PROMPT: {result["prompt"]}
RESPONSE: {response}
TOOL_TRACES: {tool_traces}

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
