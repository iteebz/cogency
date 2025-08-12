"""Heuristic utility tests."""

from cogency.utils.heuristics import (
    calc_backoff,
    needs_network_retry,
)


def test_needs_network_retry():
    assert needs_network_retry([]) is False

    assert needs_network_retry([{"error": "timeout occurred"}]) is True
    assert needs_network_retry([{"error": "rate limit exceeded"}]) is True
    assert needs_network_retry([{"error": "connection failed"}]) is True
    assert needs_network_retry([{"error": "network error"}]) is True
    assert needs_network_retry([{"error": "HTTP 429"}]) is True
    assert needs_network_retry([{"error": "HTTP 503"}]) is True
    assert needs_network_retry([{"error": "HTTP 502"}]) is True

    assert needs_network_retry([{"error": "validation error"}]) is False
    assert needs_network_retry([{"error": "invalid input"}]) is False


def test_calc_backoff():
    assert calc_backoff(0) == 1.0
    assert calc_backoff(1) == 2.0
    assert calc_backoff(2) == 4.0
    assert calc_backoff(3) == 8.0

    assert calc_backoff(0, base_delay=2.0) == 2.0
    assert calc_backoff(1, base_delay=2.0) == 4.0
    assert calc_backoff(2, base_delay=2.0) == 8.0
