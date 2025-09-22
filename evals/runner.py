"""Test execution engine - canonical implementation."""

import asyncio
import shutil
import time
import uuid
from pathlib import Path

from .config import config


async def evaluate_category(category: str, generator) -> dict:
    """Run evaluation category."""
    import random

    random.seed(config.seed)

    tests = generator(config.sample_size)
    semaphore = asyncio.Semaphore(config.max_concurrent_tests)

    async def run_test(i, test):
        async with semaphore:
            await asyncio.sleep(i * 0.2)  # Stagger requests
            return await _execute_test(i, test, category)

    results = await asyncio.gather(
        *[run_test(i, test) for i, test in enumerate(tests)], return_exceptions=True
    )

    # Process results
    final_results = [
        {"test_id": f"{category}_{i:02d}", "error": str(result), "passed": False}
        if isinstance(result, Exception)
        else result
        for i, result in enumerate(results)
    ]

    # Judge results
    judged_results = []
    for result in final_results:
        judgment = await _judge_result(result)
        result.update(judgment)
        judged_results.append(result)

    passed_count = len([r for r in judged_results if r.get("passed") is True])

    return {
        "category": category,
        "passed": passed_count,
        "total": len(judged_results),
        "rate": passed_count / len(judged_results) if judged_results else 0,
        "results": judged_results,
    }


async def _execute_test(i, test, category):
    """Execute individual test."""
    _prepare_sandbox()
    test_id = f"{category}_{i + 1:02d}"
    print(f"🧪 {test_id}")

    user_id = str(uuid.uuid4())
    start_time = time.time()
    agent = _create_agent(test)

    try:
        events, prompt_used = await _run_test(test, agent, user_id)

        tokens = _extract_metrics(events)
        stream = _format_stream(events)

        return {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "stream": stream,
            "tokens": tokens,
            "seconds": round(time.time() - start_time, 2),
            "criteria": test["criteria"],
        }

    except asyncio.TimeoutError:
        return {"test_id": f"{category}_{i:02d}", "error": "Timeout", "passed": False}
    except Exception as e:
        return {"test_id": f"{category}_{i:02d}", "error": str(e), "passed": False}
    finally:
        await _cleanup_agent(agent)


async def _run_test(test, agent, user_id):
    """Execute test based on structure."""
    chunks = test.get("chunks", False)

    if "store_prompt" in test:
        # Memory test: store -> destroy -> recall
        await _consume_stream(agent(test["store_prompt"], user_id=user_id, chunks=chunks))

        if test.get("requires_agent_destruction"):
            agent = _recreate_agent(test)

        stream = agent(test["recall_prompt"], user_id=user_id, chunks=chunks)
        return [event async for event in stream], test["recall_prompt"]

    if "conversation_prompts" in test:
        # Multi-turn conversation
        events = []
        conversation_id = str(uuid.uuid4())

        for i, prompt in enumerate(test["conversation_prompts"]):
            events.append({"type": "user", "content": prompt})
            stream = agent(prompt, user_id=user_id, conversation_id=conversation_id, chunks=chunks)
            async for event in stream:
                events.append(event)

            if i < len(test["conversation_prompts"]) - 1:
                events.append({"type": "separator", "content": "---"})

        return events, " → ".join(test["conversation_prompts"])

    # Standard single prompt
    stream = agent(test["prompt"], user_id=user_id, chunks=chunks)
    return [event async for event in stream], test["prompt"]


def _prepare_sandbox():
    """Clean sandbox between tests."""
    sandbox = Path(".sandbox")
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(exist_ok=True)


def _create_agent(test):
    """Create agent with test configuration."""
    if test.get("empty_tools"):
        return config.agent(tools=[])
    if test.get("profile"):
        return config.agent(profile=True)
    return config.agent()


def _recreate_agent(test):
    """Recreate agent after destruction."""
    import gc

    gc.collect()
    return _create_agent(test)


async def _consume_stream(stream):
    """Consume stream without processing."""
    async for _ in stream:
        pass


def _extract_metrics(events):
    """Extract token counts from events."""
    total_input = 0
    total_output = 0

    for event in events:
        if isinstance(event, dict) and event.get("type") == "metrics":
            total = event["total"]
            total_input += total["input"]
            total_output += total["output"]

    return [total_input, total_output]


def _format_stream(events):
    """Convert events to readable format."""
    return [
        f"{event['type'].upper()}: {event.get('content', '')}"
        for event in events
        if isinstance(event, dict) and event.get("type") != "metrics"
    ]


async def _judge_result(result):
    """Judge test result."""
    if result.get("error"):
        return {"passed": False, "judge_reason": f"Test error: {result['error']}"}

    if not config.judge:
        return {"passed": None, "judge_reason": "Manual review required"}

    from cogency.lib.llms import Anthropic, Gemini, OpenAI

    stream_text = "\n".join(result.get("stream", []))

    prompt = f"""Evaluate this test result:

CRITERIA: {result["criteria"]}
PROMPT: {result["prompt"]}
AGENT_STREAM:
{stream_text}

Did the agent meet the criteria? Answer PASS or FAIL with brief reason.

Format: PASS: reason | FAIL: reason"""

    try:
        judge_llms = {"openai": OpenAI, "anthropic": Anthropic, "gemini": Gemini}
        if config.judge not in judge_llms:
            return {"passed": False, "judge_reason": f"Unknown judge: {config.judge}"}

        judge = judge_llms[config.judge]()
        messages = [{"role": "user", "content": prompt}]
        response = await judge.generate(messages)

        clean = response.strip().upper()
        if clean.startswith("PASS"):
            return {"passed": True, "judge_reason": response.strip()}
        if clean.startswith("FAIL"):
            return {"passed": False, "judge_reason": response.strip()}
        return {"passed": False, "judge_reason": f"Invalid response: {response}"}

    except Exception as e:
        return {"passed": False, "judge_reason": f"Judge error: {str(e)}"}


async def _cleanup_agent(agent):
    """Clean up agent resources."""
    try:
        if (
            hasattr(agent, "config")
            and hasattr(agent.config, "llm")
            and hasattr(agent.config.llm, "close")
        ):
            await agent.config.llm.close()
    except Exception:
        pass
