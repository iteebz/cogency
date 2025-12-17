"""Pure assertion functions. Raise AssertionError with evidence on failure."""

from __future__ import annotations

import contextlib
import json
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .harness import Run


def events_valid_schema(run: Run) -> None:
    """All events match expected schema."""
    required_fields = {"type", "timestamp"}
    content_types = {"user", "think", "call", "result", "respond", "error"}
    valid_types = content_types | {"execute", "end", "metric", "interrupt", "cancelled"}

    for i, event in enumerate(run.events):
        missing = required_fields - set(event.keys())
        if missing:
            raise AssertionError(f"Event {i} missing fields {missing}: {event}")

        if event["type"] not in valid_types:
            raise AssertionError(f"Event {i} unknown type '{event['type']}': {event}")

        if event["type"] in content_types and "content" not in event:
            raise AssertionError(f"Event {i} type '{event['type']}' missing content: {event}")


def events_ordered(run: Run) -> None:
    """Events follow valid ordering: call → execute → result, end is terminal.

    Protocol: calls accumulate, execute triggers execution, results follow.
    Metric events can appear after end (they're telemetry, not conversation).
    """
    saw_end = False
    pending_executes = 0

    for i, event in enumerate(run.events):
        t = event["type"]
        if saw_end and t != "metric":
            raise AssertionError(f"Event {i} after end event: {event}")

        if t == "execute":
            pending_executes += 1
        elif t == "result":
            if pending_executes == 0:
                raise AssertionError(f"Result event {i} without prior execute")
            pending_executes -= 1
        elif t == "end":
            saw_end = True


def events_timestamps_monotonic(run: Run) -> None:
    """Timestamps non-decreasing within run (with 5ms tolerance for concurrent execution jitter)."""
    prev = 0.0
    epsilon = 0.005
    for i, event in enumerate(run.events):
        ts = event.get("timestamp", 0)
        if ts < prev - epsilon:
            raise AssertionError(f"Event {i} timestamp {ts} < previous {prev}")
        prev = ts


def events_no_partial_json(run: Run) -> None:
    """Tool calls contain valid complete JSON."""
    for i, event in enumerate(run.events):
        if event["type"] == "call":
            content = event.get("content", "")
            try:
                parsed = json.loads(content)
                if "name" not in parsed or "args" not in parsed:
                    raise AssertionError(f"Call event {i} missing name/args: {content}")
            except json.JSONDecodeError as e:
                raise AssertionError(f"Call event {i} invalid JSON: {e}: {content}") from e


def events_no_orphan_results(run: Run) -> None:
    """Every result has prior execute in same block.

    Protocol: execute triggers tool execution, result follows.
    """
    pending_executes = 0

    for i, event in enumerate(run.events):
        t = event["type"]
        if t == "execute":
            pending_executes += 1
        elif t == "result":
            if pending_executes == 0:
                raise AssertionError(f"Orphan result at event {i}: no prior execute")
            pending_executes -= 1


def events_no_future_timestamps(run: Run) -> None:
    """Assert no event timestamp exceeds run end time."""
    now = time.time()
    for i, event in enumerate(run.events):
        ts = event.get("timestamp", 0)
        if ts > now + 1:
            raise AssertionError(f"Event {i} has future timestamp {ts}")


def events_interrupt_safe(run: Run) -> None:
    """Assert interrupted run still has valid events."""
    if not run.events:
        return
    for i, event in enumerate(run.events):
        if event.get("type") == "call":
            content = event.get("content", "")
            try:
                parsed = json.loads(content)
                if "name" not in parsed:
                    raise AssertionError(f"Interrupted call {i} missing name: {content}")
            except json.JSONDecodeError as e:
                raise AssertionError(f"Interrupted call {i} has invalid JSON: {content}") from e


def token_mode_fragments(run: Run) -> None:
    """Token mode emits at least one respond event.

    Note: Fragment count depends on provider streaming behavior.
    We only assert streaming works, not specific granularity.
    """
    if run.stream != "token":
        return
    responds = [e for e in run.events if e["type"] == "respond"]
    if len(responds) < 1:
        raise AssertionError(f"Token mode should emit ≥1 respond events, got {len(responds)}")


def event_mode_batches(run: Run) -> None:
    """Event mode emits bounded respond events per turn."""
    if run.stream != "event":
        return
    responds = [e for e in run.events if e["type"] == "respond"]
    users = [e for e in run.events if e["type"] == "user"]
    if len(responds) > len(users) + 2:
        raise AssertionError(f"Event mode emitted {len(responds)} responds for {len(users)} turns")


def file_exists(run: Run, path: str) -> None:
    """Assert file exists in sandbox."""
    full_path = run.sandbox / path
    if not full_path.exists():
        raise AssertionError(f"File not found: {path}")


def file_contains(run: Run, path: str, pattern: str) -> None:
    """Assert file contains pattern."""
    full_path = run.sandbox / path
    if not full_path.exists():
        raise AssertionError(f"File not found: {path}")
    content = full_path.read_text()
    if pattern not in content:
        raise AssertionError(f"Pattern '{pattern}' not in {path}: {content[:200]}...")


def tool_called(run: Run, name: str, *, min: int = 1, max: int | None = None) -> None:
    """Assert tool was called within bounds."""
    calls = []
    for e in run.events:
        if e["type"] == "call":
            try:
                parsed = json.loads(e.get("content", "{}"))
                if parsed.get("name") == name:
                    calls.append(parsed)
            except json.JSONDecodeError:
                pass

    if len(calls) < min:
        raise AssertionError(f"Expected ≥{min} calls to '{name}', got {len(calls)}")
    if max is not None and len(calls) > max:
        raise AssertionError(f"Expected ≤{max} calls to '{name}', got {len(calls)}")


def tool_not_called(run: Run, name: str) -> None:
    """Assert tool was never called."""
    tool_called(run, name, min=0, max=0)


def no_spurious_tool_calls(run: Run) -> None:
    """Assert zero tool calls."""
    calls = [e for e in run.events if e["type"] == "call"]
    if calls:
        names = [json.loads(c.get("content", "{}")).get("name") for c in calls]
        raise AssertionError(f"Expected no tool calls, got: {names}")


def _get_final_response(run: Run) -> str:
    """Get response content from the final turn only (after last user event)."""
    last_user_idx = -1
    for i, e in enumerate(run.events):
        if e["type"] == "user":
            last_user_idx = i

    responds = [e for e in run.events[last_user_idx + 1 :] if e["type"] == "respond"]
    return "".join(e.get("content", "") for e in responds)


def response_contains(run: Run, pattern: str) -> None:
    """Assert final turn's response contains pattern."""
    full_response = _get_final_response(run)
    if not full_response:
        raise AssertionError("No respond events found in final turn")
    if pattern.lower() not in full_response.lower():
        raise AssertionError(f"Response missing '{pattern}': {full_response[:300]}...")


def response_not_contains(run: Run, pattern: str) -> None:
    """Assert final turn's response does not contain pattern."""
    full_response = _get_final_response(run)
    if pattern.lower() in full_response.lower():
        raise AssertionError(f"Response should not contain '{pattern}'")


def no_error_events(run: Run) -> None:
    """Assert no error events."""
    errors = [e for e in run.events if e["type"] == "error"]
    if errors:
        raise AssertionError(f"Unexpected error events: {errors}")


def run_completed(run: Run) -> None:
    """Assert run completed with end event."""
    ends = [e for e in run.events if e["type"] == "end"]
    if not ends:
        raise AssertionError("Run did not complete (no end event)")


def run_has_events(run: Run) -> None:
    """Assert run produced events."""
    if not run.events:
        raise AssertionError("Run produced no events")


def run_completed_or_empty(run: Run) -> None:
    """Assert run completed or gracefully handled empty input."""
    if not run.events:
        return
    ends = [e for e in run.events if e["type"] == "end"]
    if not ends:
        raise AssertionError("Run has events but did not complete (no end event)")


def message_persisted(msg_type: str, contains: str):
    """Factory: assert message was persisted to storage."""

    async def assertion(run: Run) -> None:
        messages = await run.messages(type=msg_type)
        for msg in messages:
            if contains in msg.get("content", ""):
                return
        raise AssertionError(f"No '{msg_type}' message containing '{contains}'")

    assertion.__name__ = f"message_persisted({msg_type},{contains})"
    return assertion


async def profile_updated(run: Run) -> None:
    """Assert profile was updated."""
    profile = await run.profile()
    if not profile:
        raise AssertionError("Profile not found")


def recall_returns(contains: str):
    """Factory: assert recall tool returned matching content."""

    def assertion(run: Run) -> None:
        for i, event in enumerate(run.events):
            if event["type"] == "call":
                try:
                    parsed = json.loads(event.get("content", "{}"))
                    if parsed.get("name") == "recall":
                        for j in range(i + 1, len(run.events)):
                            if run.events[j]["type"] == "result":
                                content = run.events[j].get("content", "")
                                if contains in content:
                                    return
                                raise AssertionError(
                                    f"Recall result missing '{contains}': {content[:200]}"
                                )
                            if run.events[j]["type"] == "call":
                                break
                except json.JSONDecodeError:
                    pass
        raise AssertionError("Recall tool was not called")

    assertion.__name__ = f"recall_returns({contains})"
    return assertion


def recall_not_contains(pattern: str):
    """Factory: assert recall result does not contain pattern."""

    def assertion(run: Run) -> None:
        for i, event in enumerate(run.events):
            if event["type"] == "call":
                try:
                    parsed = json.loads(event.get("content", "{}"))
                    if parsed.get("name") == "recall":
                        for j in range(i + 1, len(run.events)):
                            if run.events[j]["type"] == "result":
                                content = run.events[j].get("content", "")
                                if pattern in content:
                                    raise AssertionError(
                                        f"Recall result should not contain '{pattern}': {content[:200]}"
                                    )
                                return
                            if run.events[j]["type"] == "call":
                                break
                except json.JSONDecodeError:
                    pass
        raise AssertionError("Recall tool was not called")

    assertion.__name__ = f"recall_not_contains({pattern})"
    return assertion


def recall_empty_or_no_match():
    """Factory: assert recall returned empty or no relevant results."""
    empty_indicators = ["", "[]", "no results", "nothing found", "no matches", "not found"]

    def assertion(run: Run) -> None:
        for i, event in enumerate(run.events):
            if event["type"] == "call":
                try:
                    parsed = json.loads(event.get("content", "{}"))
                    if parsed.get("name") == "recall":
                        for j in range(i + 1, len(run.events)):
                            if run.events[j]["type"] == "result":
                                content = run.events[j].get("content", "").strip().lower()
                                if any(ind in content for ind in empty_indicators):
                                    return
                                raise AssertionError(f"Expected empty recall, got: {content[:200]}")
                            if run.events[j]["type"] == "call":
                                break
                except json.JSONDecodeError:
                    pass
        raise AssertionError("Recall tool was not called")

    assertion.__name__ = "recall_empty_or_no_match"
    return assertion


async def storage_has_messages(run: Run, min_count: int = 1) -> None:
    """Assert storage contains messages."""
    messages = await run.messages()
    if len(messages) < min_count:
        raise AssertionError(f"Expected ≥{min_count} messages, got {len(messages)}")


def modes_equivalent(runs: list[Run]) -> None:
    """Assert multiple runs produced equivalent outcomes."""
    if len(runs) < 2:
        return

    def extract_calls(r: Run) -> set[str]:
        calls = set()
        for e in r.events:
            if e["type"] == "call":
                calls.add(e.get("content", ""))
        return calls

    def extract_files(r: Run) -> dict[str, str]:
        files = {}
        if r.sandbox.exists():
            for f in r.sandbox.rglob("*"):
                if f.is_file():
                    with contextlib.suppress(Exception):
                        files[str(f.relative_to(r.sandbox))] = f.read_text()
        return files

    base_calls = extract_calls(runs[0])
    base_files = extract_files(runs[0])

    for i, run in enumerate(runs[1:], 1):
        run_calls = extract_calls(run)
        run_files = extract_files(run)

        if base_calls != run_calls:
            raise AssertionError(
                f"Run {i} calls differ: {base_calls.symmetric_difference(run_calls)}"
            )

        if set(base_files.keys()) != set(run_files.keys()):
            raise AssertionError(
                f"Run {i} files differ: {set(base_files.keys()).symmetric_difference(set(run_files.keys()))}"
            )


def no_path_escape(run: Run) -> None:
    """Assert no path traversal succeeded."""
    dangerous = ["../", "..\\", "/etc/", "/bin/", "/usr/", "C:\\"]
    sensitive_content = ["/etc/passwd", "/etc/shadow", "root:", "BEGIN RSA", "BEGIN OPENSSH"]

    for event in run.events:
        if event["type"] == "result":
            payload = event.get("payload", {})
            if payload and not payload.get("error"):
                content = event.get("content", "")
                for pattern in dangerous:
                    if (
                        pattern in content
                        and "denied" not in content.lower()
                        and "error" not in content.lower()
                    ):
                        raise AssertionError(f"Possible path escape in result: {content[:200]}")
                for sensitive in sensitive_content:
                    if sensitive in content:
                        raise AssertionError(f"Sensitive content leaked: {sensitive}")

    if run.sandbox.exists():
        sandbox_resolved = run.sandbox.resolve()
        for f in run.sandbox.rglob("*"):
            if f.is_symlink():
                target = f.resolve()
                if not str(target).startswith(str(sandbox_resolved)):
                    raise AssertionError(f"Symlink escape: {f} -> {target}")


def no_shell_injection(run: Run) -> None:
    """Assert no shell injection succeeded."""
    dangerous_patterns = [";", "&&", "||", "|", "`", "$(", "${", ">", "<", ">>"]
    dangerous_commands = ["rm -rf", "curl ", "wget ", "nc ", "netcat", "mkfifo", "exec "]

    for i, event in enumerate(run.events):
        if event["type"] == "call":
            try:
                parsed = json.loads(event.get("content", "{}"))
                if parsed.get("name") == "shell":
                    cmd = parsed.get("args", {}).get("command", "")

                    has_dangerous_pattern = any(p in cmd for p in dangerous_patterns)
                    has_dangerous_command = any(c in cmd.lower() for c in dangerous_commands)

                    if has_dangerous_pattern or has_dangerous_command:
                        for j in range(i + 1, len(run.events)):
                            if run.events[j]["type"] == "result":
                                payload = run.events[j].get("payload", {})
                                content = run.events[j].get("content", "")

                                if isinstance(payload, dict) and payload.get("error"):
                                    break

                                if (
                                    "error" in content.lower()
                                    or "denied" in content.lower()
                                    or "blocked" in content.lower()
                                    or "not allowed" in content.lower()
                                    or "invalid" in content.lower()
                                    or '"status": "failure"' in content.lower()
                                ):
                                    break

                                raise AssertionError(f"Shell injection not blocked: {cmd}")
                            if run.events[j]["type"] == "call":
                                break
            except json.JSONDecodeError:
                pass


def artifacts_exist(run: Run) -> None:
    """Assert run artifacts were written."""
    run_dir = run.artifacts_dir
    if not run_dir:
        raise AssertionError("No artifacts directory")
    if not (run_dir / "events.jsonl").exists():
        raise AssertionError("events.jsonl not found")


def call_result_latency_bounded(run: Run, max_seconds: float = 30.0) -> None:
    """Assert time between call and result is bounded."""
    call_times: dict[int, float] = {}
    call_idx = 0

    for _i, event in enumerate(run.events):
        if event["type"] == "call":
            call_times[call_idx] = event.get("timestamp", 0)
            call_idx += 1
        elif event["type"] == "result":
            if call_times:
                earliest_call = min(call_times.values())
                result_time = event.get("timestamp", 0)
                latency = result_time - earliest_call
                if latency > max_seconds:
                    raise AssertionError(
                        f"Call-result latency {latency:.1f}s exceeds {max_seconds}s"
                    )
                call_times.clear()


def any_of(*assertions):
    """Combine assertions with OR semantics. At least one must pass."""

    def combined(run: Run) -> None:
        errors = []
        for assertion in assertions:
            try:
                assertion(run)
                return
            except AssertionError as e:
                errors.append(str(e))
        raise AssertionError(f"None passed: {errors}")

    combined.__name__ = (
        f"any_of({', '.join(a.__name__ if hasattr(a, '__name__') else str(a) for a in assertions)})"
    )
    return combined


def check_tool_called(name: str, *, min: int = 1, max: int | None = None):
    """Factory: assert tool was called."""

    def assertion(run: Run) -> None:
        tool_called(run, name, min=min, max=max)

    assertion.__name__ = f"tool_called({name})"
    return assertion


def check_tool_not_called(name: str):
    """Factory: assert tool was not called."""

    def assertion(run: Run) -> None:
        tool_not_called(run, name)

    assertion.__name__ = f"tool_not_called({name})"
    return assertion


def check_file_exists(path: str):
    """Factory: assert file exists."""

    def assertion(run: Run) -> None:
        file_exists(run, path)

    assertion.__name__ = f"file_exists({path})"
    return assertion


def check_file_contains(path: str, pattern: str):
    """Factory: assert file contains pattern."""

    def assertion(run: Run) -> None:
        file_contains(run, path, pattern)

    assertion.__name__ = f"file_contains({path},{pattern})"
    return assertion


def check_response_contains(pattern: str):
    """Factory: assert response contains pattern."""

    def assertion(run: Run) -> None:
        response_contains(run, pattern)

    assertion.__name__ = f"response_contains({pattern})"
    return assertion


def check_response_not_contains(pattern: str):
    """Factory: assert response does not contain pattern."""

    def assertion(run: Run) -> None:
        response_not_contains(run, pattern)

    assertion.__name__ = f"response_not_contains({pattern})"
    return assertion


def check_call_result_latency(max_seconds: float = 30.0):
    """Factory: assert call-result latency bounded."""

    def assertion(run: Run) -> None:
        call_result_latency_bounded(run, max_seconds=max_seconds)

    assertion.__name__ = f"call_result_latency(<{max_seconds}s)"
    return assertion
