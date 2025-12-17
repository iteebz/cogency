# Evals

88 cases covering all Cogency invariants. 84 mechanical, 4 behavioral.

## Contract

**Assertions** = invariants (must hold for all valid executions)
**Rubrics** = acceptability (LLM judge grades quality)

### Rules

1. Assertions encode invariants only - if it can fail while system is correct, it's not an assertion
2. Judges cannot overrule assertions: `assertion FAIL → case FAIL` always
3. No LLM calls inside assertions - pure and deterministic only
4. No weakening assertions to fix flakiness - fix the cause
5. Model variance (wording, tool choice) is behavioral, not mechanical
6. Artifacts (events.jsonl, state, sandbox) are the source of truth - never judge flattened logs

### Litmus

- "Could a broken system now pass?" → you hacked the evals
- "Would a human say it's broken?" No → not a mechanical assertion

## Quick Start

```bash
poetry run python -m evals --validate                    # Validate case inventory
poetry run python -m evals --list                        # List all cases
poetry run python -m evals --cases foo bar               # Run specific cases
poetry run python -m evals --tag security --concurrency 4
poetry run python -m evals --mechanical --concurrency 8
poetry run python -m evals --behavioral --judge
```

## Structure

```
assertions.py   Pure functions, raise AssertionError with evidence
cases.py        Case definitions with prompts, assertions, setup/teardown
harness.py      Execution: Run, Verdict, sandbox isolation
judge.py        LLM judge for behavioral cases (gated, retries, consensus)
```

## Cases

```python
Case(
    name="write_creates_file",
    prompt="Write a file called test.txt containing 'hello world'",
    assertions=[
        A.check_tool_called("write"),
        A.check_file_exists("test.txt"),
        A.check_file_contains("test.txt", "hello"),
    ],
    setup=lambda: _create_file("existing.txt", "content"),
    matrix=["replay", "resume"],
    tags=["tool", "write"],
)
```

## Tags

`event`, `tool`, `security`, `memory`, `behavioral`, `boundary`, `honesty`

## Artifacts

```
.cogency/evals/runs/{run_id}/{case}/{mode}/
  events.jsonl
  state.db
  verdict.json
```

## Adding Cases

1. Add to `_*_cases()` in `cases.py`
2. Update `EXPECTED_CASE_COUNT`
3. Run `poetry run python -m evals --validate`
4. Mechanical assertions only. If behavior needs judgment, add rubric.
