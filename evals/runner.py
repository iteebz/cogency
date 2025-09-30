"""Test execution engine."""

import asyncio
import shutil
import time
import uuid
from pathlib import Path

from cogency import Agent

from .case import Case, Memory, Multi
from .judge import judge


async def run_category(category: str, cases: list[Case], agent_kwargs: dict, judge_llm) -> dict:
    """Run evaluation category."""
    semaphore = asyncio.Semaphore(agent_kwargs.pop("concurrency", 2))

    async def run_test(i, case):
        async with semaphore:
            await asyncio.sleep(i * 0.2)
            return await _execute(i, case, category, agent_kwargs)

    results = await asyncio.gather(
        *[run_test(i, case) for i, case in enumerate(cases)], return_exceptions=True
    )

    final_results = [
        {"test_id": f"{category}_{i:02d}", "error": str(result), "passed": False}
        if isinstance(result, Exception)
        else result
        for i, result in enumerate(results)
    ]

    judged_results = []
    for result in final_results:
        judgment = await judge(result, judge_llm)
        result["passed"] = judgment.passed
        result["judge_reason"] = judgment.reason
        judged_results.append(result)

    passed_count = len([r for r in judged_results if r.get("passed") is True])

    total_tokens = sum(sum(r.get("tokens", [0, 0])) for r in judged_results)
    total_runtime = sum(r.get("seconds", 0) for r in judged_results)
    avg_tokens = total_tokens / len(judged_results) if judged_results else 0
    avg_runtime = total_runtime / len(judged_results) if judged_results else 0

    return {
        "category": category,
        "passed": passed_count,
        "total": len(judged_results),
        "rate": passed_count / len(judged_results) if judged_results else 0,
        "tokens": {"total": total_tokens, "avg": int(avg_tokens)},
        "runtime": {"total": round(total_runtime, 2), "avg": round(avg_runtime, 2)},
        "results": judged_results,
    }


async def _execute(i, case: Case, category: str, agent_kwargs: dict):
    """Execute individual test."""
    _clean_sandbox()
    test_id = f"{category}_{i + 1:02d}"
    print(f"🧪 {test_id}")

    user_id = str(uuid.uuid4())
    start_time = time.time()

    kwargs = agent_kwargs.copy()
    if case.empty_tools:
        kwargs["tools"] = []
    if case.profile:
        kwargs["profile"] = True

    agent = Agent(**kwargs)

    try:
        if isinstance(case, Memory):
            events, prompt_used = await _run_memory(case, agent, user_id)
        elif isinstance(case, Multi):
            events, prompt_used = await _run_multi(case, agent, user_id)
        else:
            events, prompt_used = await _run_single(case, agent, user_id)

        tokens = _extract_tokens(events)
        stream = _format_stream(events)

        return {
            "test_id": f"{category}_{i:02d}",
            "prompt": prompt_used,
            "stream": stream,
            "tokens": tokens,
            "seconds": round(time.time() - start_time, 2),
            "criteria": case.criteria,
        }

    except asyncio.TimeoutError:
        return {"test_id": f"{category}_{i:02d}", "error": "Timeout", "passed": False}
    except Exception as e:
        return {"test_id": f"{category}_{i:02d}", "error": str(e), "passed": False}
    finally:
        await _cleanup(agent)


async def _run_single(case: Case, agent: Agent, user_id: str):
    """Run single prompt test."""
    stream = agent(case.prompt, user_id=user_id, chunks=case.chunks)
    return [event async for event in stream], case.prompt


async def _run_memory(case: Memory, agent: Agent, user_id: str):
    """Run memory test: store -> destroy -> recall."""
    await _consume(agent(case.store, user_id=user_id, chunks=case.chunks))

    agent = Agent(
        llm=agent.config.llm,
        storage=agent.config.storage,
        tools=agent.config.tools,
        mode=agent.config.mode,
        profile=True,
    )

    stream = agent(case.recall, user_id=user_id, chunks=case.chunks)
    return [event async for event in stream], case.recall


async def _run_multi(case: Multi, agent: Agent, user_id: str):
    """Run multi-turn conversation."""
    events = []
    conversation_id = str(uuid.uuid4())

    for i, prompt in enumerate(case.prompts):
        events.append({"type": "user", "content": prompt})
        stream = agent(prompt, user_id=user_id, conversation_id=conversation_id, chunks=case.chunks)
        async for event in stream:
            events.append(event)

        if i < len(case.prompts) - 1:
            events.append({"type": "separator", "content": "---"})

    return events, " → ".join(case.prompts)


def _clean_sandbox():
    """Clean sandbox between tests."""
    sandbox = Path(".sandbox")
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(exist_ok=True)


async def _consume(stream):
    """Consume stream without processing."""
    async for _ in stream:
        pass


def _extract_tokens(events):
    """Extract token counts from events."""
    metrics = [e["total"] for e in events if isinstance(e, dict) and e.get("type") == "metrics"]
    return (
        [sum(m["input"] for m in metrics), sum(m["output"] for m in metrics)] if metrics else [0, 0]
    )


def _format_stream(events):
    """Convert events to readable format."""
    return [
        f"{e['type'].upper()}: {e.get('content', '')}"
        for e in events
        if isinstance(e, dict) and e.get("type") != "metrics"
    ]


async def _cleanup(agent):
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
