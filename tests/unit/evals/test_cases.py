"""Unit tests for eval cases."""

from __future__ import annotations

import pytest


def test_case_count():
    from evals.cases import EXPECTED_CASE_COUNT, all_cases

    assert len(all_cases()) == EXPECTED_CASE_COUNT


def test_no_duplicate_names():
    from evals.cases import all_cases

    names = [c.name for c in all_cases()]
    dupes = [n for n in names if names.count(n) > 1]
    assert not dupes, f"Duplicate names: {set(dupes)}"


def test_required_tags_covered():
    from evals.cases import REQUIRED_TAGS, all_cases

    all_tags = {tag for c in all_cases() for tag in c.tags}
    missing = REQUIRED_TAGS - all_tags
    assert not missing, f"Missing tags: {missing}"


def test_all_cases_testable():
    from evals.cases import all_cases

    for case in all_cases():
        assert case.assertions or case.rubric, f"{case.name}: no assertions or rubric"


def test_validate_cases():
    from evals.cases import validate_cases

    validate_cases()


def test_mechanical_behavioral_partition():
    from evals.cases import all_cases, behavioral_cases, mechanical_cases

    assert len(mechanical_cases()) + len(behavioral_cases()) == len(all_cases())


def test_behavioral_have_rubric():
    from evals.cases import behavioral_cases

    for c in behavioral_cases():
        assert c.rubric, f"{c.name}: behavioral but no rubric"


def test_mechanical_no_rubric():
    from evals.cases import mechanical_cases

    for c in mechanical_cases():
        assert not c.rubric, f"{c.name}: mechanical but has rubric"


@pytest.mark.asyncio
async def test_create_file_in_sandbox(tmp_path):
    from evals.cases import _create_file
    from evals.harness import _run_setup_in_sandbox

    await _run_setup_in_sandbox(lambda: _create_file("x.txt", "data"), tmp_path)
    assert (tmp_path / "x.txt").read_text() == "data"


@pytest.mark.asyncio
async def test_create_nested_dir_in_sandbox(tmp_path):
    from evals.cases import _create_dir
    from evals.harness import _run_setup_in_sandbox

    await _run_setup_in_sandbox(lambda: _create_dir("a/b/c"), tmp_path)
    assert (tmp_path / "a/b/c").is_dir()
