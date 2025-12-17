"""Unit tests for judge module."""

from __future__ import annotations

import pytest

from evals.judge import Score, _consensus_score, parse_score


def test_parse_score_pass():
    response = """VERDICT: PASS
REASON: All requirements met
CONFIDENCE: 0.95"""
    score = parse_score(response)
    assert score.passed is True
    assert score.reasons == ["All requirements met"]
    assert score.confidence == 0.95


def test_parse_score_fail():
    response = """VERDICT: FAIL
REASON: Missing tests
CONFIDENCE: 0.8"""
    score = parse_score(response)
    assert score.passed is False
    assert "Missing tests" in score.reasons[0]


def test_parse_score_missing_confidence_defaults():
    response = """VERDICT: PASS
REASON: Good job"""
    assert parse_score(response).confidence == 0.5


def test_parse_score_invalid_confidence_defaults():
    response = """VERDICT: PASS
REASON: Test
CONFIDENCE: 1.5"""
    assert parse_score(response).confidence == 0.5


def test_parse_score_malformed_fails():
    assert parse_score("random garbage").passed is False


def test_parse_score_fallback_detection():
    assert parse_score("The test PASSED").passed is True


def test_parse_score_pass_before_fail_wins():
    assert parse_score("PASS then FAIL").passed is True


def test_parse_score_empty():
    assert parse_score("").passed is False


def test_consensus_empty():
    score = _consensus_score([])
    assert score.passed is False
    assert score.confidence == 0.0


def test_consensus_single():
    scores = [Score(passed=True, reasons=["good"], confidence=0.9)]
    assert _consensus_score(scores).passed is True


def test_consensus_majority_wins():
    scores = [
        Score(passed=True, reasons=["a"], confidence=0.8),
        Score(passed=True, reasons=["b"], confidence=0.7),
        Score(passed=False, reasons=["c"], confidence=0.6),
    ]
    assert _consensus_score(scores).passed is True


def test_consensus_tie_fails():
    scores = [
        Score(passed=True, reasons=["a"], confidence=0.8),
        Score(passed=False, reasons=["b"], confidence=0.7),
    ]
    assert _consensus_score(scores).passed is False


def test_consensus_averages_confidence():
    scores = [
        Score(passed=True, reasons=["a"], confidence=0.8),
        Score(passed=True, reasons=["b"], confidence=0.6),
    ]
    assert _consensus_score(scores).confidence == pytest.approx(0.7)
