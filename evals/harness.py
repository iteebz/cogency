"""Eval harness. Run case → emit artifacts → check assertions → verdict."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import shutil
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cogency import Agent
from cogency.context import wait_for_background_tasks
from cogency.core.config import Security
from cogency.lib.sqlite import SQLite

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cogency.core.protocols import Event, Storage

    from .cases import Case

DEFAULT_USER_ID = "eval"


@dataclass
class Run:
    """Execution result with query surface."""

    id: str
    case_name: str
    mode: str
    stream: str
    events: list[Event]
    sandbox: Path
    artifacts_dir: Path | None
    duration: float
    error: str | None
    config: dict[str, Any]
    user_id: str = DEFAULT_USER_ID

    _storage: Storage | None = field(default=None, repr=False)

    async def messages(self, type: str | None = None) -> list[dict]:
        """Query persisted messages."""
        if not self._storage:
            return []
        return await self._storage.load_messages(
            conversation_id=self.id,
            user_id=self.user_id,
            include=[type] if type else None,
        )

    async def profile(self) -> dict | None:
        """Query user profile."""
        if not self._storage:
            return None
        return await self._storage.load_profile(self.user_id)

    async def tool_calls(self) -> list[dict]:
        """Query parsed tool calls."""
        calls = []
        for event in self.events:
            if event.get("type") == "call":
                try:
                    parsed = json.loads(event.get("content", "{}"))
                    calls.append(parsed)
                except json.JSONDecodeError:
                    pass
        return calls


@dataclass
class Failure:
    """Assertion failure with evidence."""

    assertion: str
    error: str
    mode: str
    evidence: dict[str, Any] | None = None


if TYPE_CHECKING:
    from .judge import Score


@dataclass
class Verdict:
    """Case verdict."""

    case: str
    passed: bool
    failures: list[Failure]
    score: Score | None = None
    runs: list[Run] = field(default_factory=list)
    duration: float = 0.0


async def execute(
    prompt: str | list[str],
    *,
    mode: str = "replay",
    stream: str = "event",
    config: dict[str, Any] | None = None,
    run_id: str | None = None,
    sandbox: Path | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> Run:
    """Execute single prompt or multi-turn conversation."""

    run_id = run_id or str(uuid.uuid4())[:8]
    sandbox = sandbox or Path(".cogency/sandbox")
    config = config or {}

    sandbox.mkdir(parents=True, exist_ok=True)

    if config.get("use_seed_storage"):
        store_path = sandbox / ".store_seed.db"
    elif config.get("storage_path"):
        store_path = Path(config["storage_path"])
    else:
        store_path = sandbox / f".store_{run_id}.db"
    storage = SQLite(str(store_path))

    llm = config.get("llm", "openai")
    tools = config.get("tools", None)
    profile = config.get("profile", False)
    profile_cadence = config.get("profile_cadence", 5)
    max_iterations = config.get("max_iterations", 10)
    history_window = config.get("history_window", None)

    security = Security(sandbox_dir=str(sandbox))

    agent_kwargs = {
        "llm": llm,
        "storage": storage,
        "mode": mode,
        "max_iterations": max_iterations,
        "profile": profile,
        "profile_cadence": profile_cadence,
        "security": security,
    }

    if tools is not None:
        agent_kwargs["tools"] = tools
    if history_window is not None:
        agent_kwargs["history_window"] = history_window

    agent = Agent(**agent_kwargs)

    events: list[Event] = []
    error: str | None = None
    start_time = time.time()

    prompts = [prompt] if isinstance(prompt, str) else prompt
    conversation_id = run_id

    try:
        for p in prompts:
            if not p:
                continue
            stream_mode = config.get("stream", stream)
            async for event in agent(
                p,
                user_id=user_id,
                conversation_id=conversation_id,
                stream=stream_mode,
            ):
                events.append(event)  # type: ignore[arg-type]
    except Exception as e:
        error = str(e)

    duration = time.time() - start_time

    return Run(
        id=run_id,
        case_name="",
        mode=mode,
        stream=config.get("stream", stream),
        events=events,
        sandbox=sandbox,
        artifacts_dir=None,
        duration=duration,
        error=error,
        config=config,
        user_id=user_id,
        _storage=storage,
    )


def write_artifacts(run: Run, artifacts_dir: Path) -> None:
    """Write run artifacts to disk."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    events_path = artifacts_dir / "events.jsonl"
    with events_path.open("w") as f:
        f.writelines(json.dumps(event) + "\n" for event in run.events)

    if run.sandbox.exists():
        state_db = run.sandbox / f".store_{run.id}.db"
        if state_db.exists():
            shutil.copy(state_db, artifacts_dir / "state.db")

    run.artifacts_dir = artifacts_dir


def write_verdict(verdict: Verdict, artifacts_dir: Path) -> None:
    """Write verdict to disk."""
    verdict_path = artifacts_dir / "verdict.json"
    verdict_data = {
        "case": verdict.case,
        "passed": verdict.passed,
        "failures": [
            {
                "assertion": f.assertion,
                "error": f.error,
                "mode": f.mode,
                "evidence": f.evidence,
            }
            for f in verdict.failures
        ],
        "score": (
            {
                "passed": verdict.score.passed,
                "reasons": verdict.score.reasons,
                "confidence": verdict.score.confidence,
            }
            if verdict.score
            else None
        ),
        "duration": verdict.duration,
        "runs": [
            {
                "id": r.id,
                "mode": r.mode,
                "stream": r.stream,
                "event_count": len(r.events),
                "duration": r.duration,
                "error": r.error,
            }
            for r in verdict.runs
        ],
    }
    with verdict_path.open("w") as f:
        json.dump(verdict_data, f, indent=2)


async def run_case(
    case: Case,
    *,
    artifacts_base: Path | None = None,
    judge: bool = False,
) -> Verdict:
    """Run case across matrix, check assertions, optionally judge."""

    case_uuid = uuid.uuid4().hex
    run_id = f"{int(time.time() * 1000)}_{case_uuid[:8]}_{case.name}"
    artifacts_base = artifacts_base or Path(".cogency/evals/runs")
    case_artifacts = artifacts_base / run_id

    failures: list[Failure] = []
    runs: list[Run] = []
    start_time = time.time()

    sandbox_base = Path(".cogency/sandboxes")
    sandbox = sandbox_base / case_uuid

    try:
        sandbox_base.mkdir(parents=True, exist_ok=True)
        sandbox.mkdir(exist_ok=False)
    except FileExistsError:
        case_uuid = f"{case_uuid}_{uuid.uuid4().hex[:8]}"
        sandbox = sandbox_base / case_uuid
        sandbox.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return Verdict(
            case=case.name,
            passed=False,
            failures=[Failure(assertion="sandbox_init", error=str(e), mode="setup")],
        )

    try:
        for mode in case.matrix:
            mode_sandbox = sandbox / mode
            if mode_sandbox.exists():
                shutil.rmtree(mode_sandbox)
            mode_sandbox.mkdir(parents=True, exist_ok=True)

            if case.setup:
                try:
                    await _run_setup_in_sandbox(case.setup, mode_sandbox)
                except Exception as e:
                    failures.append(
                        Failure(
                            assertion="setup",
                            error=str(e),
                            mode=mode,
                        )
                    )
                    continue

            config = case.config.copy() if case.config else {}

            run = await execute(
                case.prompt,
                mode=mode,
                config=config,
                sandbox=mode_sandbox,
            )
            run.case_name = case.name

            mode_artifacts = case_artifacts / mode
            write_artifacts(run, mode_artifacts)
            runs.append(run)

            if run.error:
                failures.append(
                    Failure(
                        assertion="execution",
                        error=run.error,
                        mode=mode,
                    )
                )
                continue

            if config.get("profile"):
                await wait_for_background_tasks(timeout=5.0)

            for assertion in case.assertions:
                try:
                    result = assertion(run)
                    if asyncio.iscoroutine(result):
                        await result
                except AssertionError as e:
                    failures.append(
                        Failure(
                            assertion=_assertion_name(assertion),
                            error=str(e),
                            mode=mode,
                            evidence=_extract_evidence(run, assertion),
                        )
                    )
                except Exception as e:
                    failures.append(
                        Failure(
                            assertion=_assertion_name(assertion),
                            error=f"Unexpected error: {e}",
                            mode=mode,
                        )
                    )

            if case.teardown:
                with contextlib.suppress(Exception):
                    case.teardown()
    finally:
        try:
            if sandbox.exists():
                shutil.rmtree(sandbox)
        except Exception as e:
            logger.debug(f"Sandbox cleanup failed: {e}")

    if len(runs) > 1 and not failures:
        from . import assertions as A

        try:
            A.modes_equivalent(runs)
        except AssertionError as e:
            failures.append(
                Failure(
                    assertion="modes_equivalent",
                    error=str(e),
                    mode="cross-mode",
                )
            )

    score: Score | None = None
    if not failures and case.rubric and judge:
        from .judge import judge as judge_fn

        score = await judge_fn(runs[0], case.rubric)

    duration = time.time() - start_time

    verdict = Verdict(
        case=case.name,
        passed=len(failures) == 0 and (score is None or score.passed),
        failures=failures,
        score=score,
        runs=runs,
        duration=duration,
    )

    write_verdict(verdict, case_artifacts)

    return verdict


def _assertion_name(assertion) -> str:
    """Extract meaningful name from assertion, handling lambdas."""
    if hasattr(assertion, "__name__"):
        name = assertion.__name__
        if name != "<lambda>":
            return name
    if hasattr(assertion, "__code__"):
        code = assertion.__code__
        if code.co_freevars:
            return f"lambda[{','.join(code.co_freevars)}]"
        filename = code.co_filename.split("/")[-1]
        return f"lambda@{filename}:{code.co_firstlineno}"
    return str(assertion)


def _extract_evidence(run: Run, assertion) -> dict[str, Any] | None:
    """Extract relevant evidence for failed assertion."""
    evidence: dict[str, Any] = {}

    name = assertion.__name__ if hasattr(assertion, "__name__") else ""

    if "event" in name.lower():
        evidence["event_types"] = [e.get("type") for e in run.events[:20]]
        evidence["event_count"] = len(run.events)

    if "tool" in name.lower() or "call" in name.lower():
        calls = []
        for e in run.events:
            if e.get("type") == "call":
                try:
                    calls.append(json.loads(e.get("content", "{}")))
                except json.JSONDecodeError:
                    calls.append(e.get("content"))
        evidence["tool_calls"] = calls[:10]

    if "file" in name.lower() and run.sandbox.exists():
        evidence["sandbox_files"] = [
            str(f.relative_to(run.sandbox))
            for f in run.sandbox.rglob("*")
            if f.is_file() and not f.name.startswith(".store_")
        ][:20]

    if "response" in name.lower() or "respond" in name.lower():
        responds = [e for e in run.events if e.get("type") == "respond"]
        full = "".join(e.get("content", "") for e in responds)
        evidence["response_preview"] = full[:500]

    return evidence if evidence else None


_sandbox_context: ContextVar[Path | None] = ContextVar("sandbox_context", default=None)


async def _run_setup_in_sandbox(setup_fn, sandbox: Path) -> None:
    """Run setup function with sandbox path available."""
    token = _sandbox_context.set(sandbox)
    try:
        result = setup_fn()
        if asyncio.iscoroutine(result):
            await result
    finally:
        _sandbox_context.reset(token)


def get_sandbox() -> Path:
    """Get current sandbox path for setup functions."""
    sandbox = _sandbox_context.get()
    if sandbox is None:
        return Path(".cogency/sandbox")
    return sandbox


async def run_suite(
    cases: list[Case],
    *,
    concurrency: int = 2,
    artifacts_base: Path | None = None,
    judge: bool = False,
) -> dict[str, Any]:
    """Run suite of cases with concurrency control."""

    artifacts_base = artifacts_base or Path(".cogency/evals/runs")
    run_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    suite_dir = artifacts_base / run_id

    semaphore = asyncio.Semaphore(concurrency)

    async def run_with_semaphore(case: Case) -> Verdict:
        async with semaphore:
            return await run_case(
                case,
                artifacts_base=suite_dir,
                judge=judge,
            )

    verdicts = await asyncio.gather(
        *[run_with_semaphore(case) for case in cases],
        return_exceptions=True,
    )

    results = []
    for i, v in enumerate(verdicts):
        if isinstance(v, Exception):
            results.append(
                Verdict(
                    case=cases[i].name,
                    passed=False,
                    failures=[
                        Failure(
                            assertion="harness",
                            error=str(v),
                            mode="unknown",
                        )
                    ],
                )
            )
        else:
            results.append(v)

    passed = sum(1 for v in results if v.passed)
    failed = len(results) - passed

    summary = {
        "run_id": run_id,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "rate": f"{passed / len(results):.1%}" if results else "0%",
        "verdicts": [
            {
                "case": v.case,
                "passed": v.passed,
                "failure_count": len(v.failures),
                "duration": v.duration,
            }
            for v in results
        ],
    }

    summary_path = suite_dir / "summary.json"
    suite_dir.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    return summary
