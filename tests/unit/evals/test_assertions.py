"""Negative tests for eval assertions."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.harness import Run


def make_run(events: list[dict] | None = None, **kwargs) -> Run:
    defaults = {
        "id": "test",
        "case_name": "test",
        "mode": "replay",
        "stream": "event",
        "events": events or [],
        "sandbox": Path("/tmp/nonexistent"),
        "artifacts_dir": None,
        "duration": 1.0,
        "error": None,
        "config": {},
        "user_id": "eval",
    }
    defaults.update(kwargs)
    return Run(**defaults)


def test_events_valid_schema_passes():
    from evals.assertions import events_valid_schema

    run = make_run(
        events=[
            {"type": "user", "timestamp": 1.0, "content": "hello"},
            {"type": "respond", "timestamp": 2.0, "content": "hi"},
            {"type": "end", "timestamp": 3.0},
        ]
    )
    events_valid_schema(run)


def test_events_valid_schema_fails_missing_type():
    from evals.assertions import events_valid_schema

    run = make_run(events=[{"timestamp": 1.0, "content": "hello"}])
    with pytest.raises(AssertionError, match="missing fields"):
        events_valid_schema(run)


def test_events_valid_schema_fails_missing_timestamp():
    from evals.assertions import events_valid_schema

    run = make_run(events=[{"type": "user", "content": "hello"}])
    with pytest.raises(AssertionError, match="missing fields"):
        events_valid_schema(run)


def test_events_valid_schema_fails_unknown_type():
    from evals.assertions import events_valid_schema

    run = make_run(events=[{"type": "bogus", "timestamp": 1.0}])
    with pytest.raises(AssertionError, match="unknown type"):
        events_valid_schema(run)


def test_events_valid_schema_fails_content_type_missing_content():
    from evals.assertions import events_valid_schema

    run = make_run(events=[{"type": "user", "timestamp": 1.0}])
    with pytest.raises(AssertionError, match="missing content"):
        events_valid_schema(run)


def test_tool_called_passes():
    from evals.assertions import tool_called

    run = make_run(
        events=[{"type": "call", "timestamp": 1.0, "content": '{"name": "write", "args": {}}'}]
    )
    tool_called(run, "write")


def test_tool_called_fails_not_called():
    from evals.assertions import tool_called

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "done"}])
    with pytest.raises(AssertionError, match="Expected ≥1 calls"):
        tool_called(run, "write")


def test_tool_called_fails_wrong_tool():
    from evals.assertions import tool_called

    run = make_run(
        events=[{"type": "call", "timestamp": 1.0, "content": '{"name": "read", "args": {}}'}]
    )
    with pytest.raises(AssertionError, match="Expected ≥1 calls"):
        tool_called(run, "write")


def test_tool_not_called_passes():
    from evals.assertions import tool_not_called

    run = make_run(events=[])
    tool_not_called(run, "write")


def test_tool_not_called_fails():
    from evals.assertions import tool_not_called

    run = make_run(
        events=[{"type": "call", "timestamp": 1.0, "content": '{"name": "write", "args": {}}'}]
    )
    with pytest.raises(AssertionError, match="Expected ≤0 calls"):
        tool_not_called(run, "write")


def test_response_contains_passes():
    from evals.assertions import response_contains

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "The answer is 42"}])
    response_contains(run, "42")


def test_response_contains_fails_missing():
    from evals.assertions import response_contains

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "The answer is 42"}])
    with pytest.raises(AssertionError, match="missing"):
        response_contains(run, "43")


def test_response_contains_fails_no_events():
    from evals.assertions import response_contains

    run = make_run(events=[])
    with pytest.raises(AssertionError, match="No respond events"):
        response_contains(run, "anything")


def test_response_not_contains_passes():
    from evals.assertions import response_not_contains

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "The answer is 42"}])
    response_not_contains(run, "43")


def test_response_not_contains_fails():
    from evals.assertions import response_not_contains

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "The answer is 42"}])
    with pytest.raises(AssertionError, match="should not contain"):
        response_not_contains(run, "42")


def test_run_completed_passes():
    from evals.assertions import run_completed

    run = make_run(events=[{"type": "end", "timestamp": 1.0}])
    run_completed(run)


def test_run_completed_fails():
    from evals.assertions import run_completed

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "hi"}])
    with pytest.raises(AssertionError, match="no end event"):
        run_completed(run)


def test_any_of_passes():
    from evals.assertions import any_of, run_completed, run_has_events

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "hi"}])
    any_of(run_completed, run_has_events)(run)


def test_any_of_fails():
    from evals.assertions import any_of, run_completed

    run = make_run(events=[])
    with pytest.raises(AssertionError, match="None passed"):
        any_of(run_completed, run_completed)(run)


def test_no_spurious_tool_calls_passes():
    from evals.assertions import no_spurious_tool_calls

    run = make_run(events=[{"type": "respond", "timestamp": 1.0, "content": "done"}])
    no_spurious_tool_calls(run)


def test_no_spurious_tool_calls_fails():
    from evals.assertions import no_spurious_tool_calls

    run = make_run(
        events=[{"type": "call", "timestamp": 1.0, "content": '{"name": "search", "args": {}}'}]
    )
    with pytest.raises(AssertionError, match="Expected no tool calls"):
        no_spurious_tool_calls(run)


def test_events_ordered_passes():
    from evals.assertions import events_ordered

    run = make_run(
        events=[
            {"type": "call", "timestamp": 1.0, "content": '{"name": "x", "args": {}}'},
            {"type": "execute", "timestamp": 1.5},
            {"type": "result", "timestamp": 2.0, "content": "ok"},
            {"type": "end", "timestamp": 3.0},
        ]
    )
    events_ordered(run)


def test_events_ordered_fails_result_before_call():
    from evals.assertions import events_ordered

    run = make_run(events=[{"type": "result", "timestamp": 1.0, "content": "orphan"}])
    with pytest.raises(AssertionError, match="without prior execute"):
        events_ordered(run)


def test_events_ordered_fails_event_after_end():
    from evals.assertions import events_ordered

    run = make_run(
        events=[
            {"type": "end", "timestamp": 1.0},
            {"type": "respond", "timestamp": 2.0, "content": "after end"},
        ]
    )
    with pytest.raises(AssertionError, match="after end event"):
        events_ordered(run)
