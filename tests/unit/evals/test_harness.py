"""Unit tests for eval harness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness import Run


def make_run(events: list[dict] | None = None, **kwargs) -> Run:
    defaults = {
        "id": "test_run",
        "case_name": "test_case",
        "mode": "replay",
        "stream": "event",
        "events": events or [],
        "sandbox": Path("/tmp/test_sandbox"),
        "artifacts_dir": None,
        "duration": 1.5,
        "error": None,
        "config": {},
        "user_id": "eval",
    }
    defaults.update(kwargs)
    return Run(**defaults)


def test_write_artifacts_creates_valid_jsonl(tmp_path):
    from evals.harness import write_artifacts

    run = make_run(
        sandbox=tmp_path / "sandbox",
        events=[
            {"type": "user", "timestamp": 1.0, "content": "hello"},
            {"type": "respond", "timestamp": 2.0, "content": "hi"},
        ],
    )
    run.sandbox.mkdir(parents=True)

    write_artifacts(run, tmp_path / "artifacts")

    lines = (tmp_path / "artifacts" / "events.jsonl").read_text().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        json.loads(line)


def test_write_verdict_serializes_all_fields(tmp_path):
    from evals.harness import Failure, Verdict, write_verdict
    from evals.judge import Score

    verdict = Verdict(
        case="test",
        passed=False,
        failures=[Failure(assertion="x", error="y", mode="z", evidence={"k": "v"})],
        score=Score(passed=False, reasons=["bad"], confidence=0.8),
        runs=[make_run()],
        duration=2.5,
    )

    write_verdict(verdict, tmp_path)

    data = json.loads((tmp_path / "verdict.json").read_text())
    assert data["failures"][0]["evidence"] == {"k": "v"}
    assert data["score"]["confidence"] == 0.8


@pytest.mark.asyncio
async def test_context_isolated_during_setup(tmp_path):
    from evals.harness import _run_setup_in_sandbox, get_sandbox

    captured = None

    def setup():
        nonlocal captured
        captured = get_sandbox()

    await _run_setup_in_sandbox(setup, tmp_path)
    assert captured == tmp_path
    assert get_sandbox() == Path(".cogency/sandbox")


@pytest.mark.asyncio
async def test_context_resets_on_exception(tmp_path):
    from evals.harness import _run_setup_in_sandbox, get_sandbox

    def raise_error():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await _run_setup_in_sandbox(raise_error, tmp_path)

    assert get_sandbox() == Path(".cogency/sandbox")


def test_assertion_name_returns_function_name():
    from evals.harness import _assertion_name

    def my_custom_assertion(r):
        return r

    name = _assertion_name(my_custom_assertion)
    assert name == "my_custom_assertion"


def test_assertion_name_lambda_includes_line():
    from evals.harness import _assertion_name

    fn = lambda r: None  # noqa: E731
    name = _assertion_name(fn)
    assert ":" in name or "lambda" in name
