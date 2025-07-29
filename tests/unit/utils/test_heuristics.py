"""Heuristic utility tests."""

from cogency.utils.heuristics import (
    calc_backoff,
    is_simple_query,
    needs_network_retry,
    query_needs_tools,
)


def test_is_simple_query():
    assert is_simple_query("hello") is True
    assert is_simple_query("hello world") is True
    assert is_simple_query("hello world test") is False
    assert is_simple_query("hello?") is False
    assert is_simple_query("hello!") is False
    assert is_simple_query("") is True


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


def test_query_needs_tools():
    tools = ["search", "calculator"]
    no_tools = []

    assert query_needs_tools("search for information", tools) is False
    assert query_needs_tools("search for information", no_tools) is True
    assert query_needs_tools("find the answer", no_tools) is True
    assert query_needs_tools("look up details", no_tools) is True
    assert query_needs_tools("scrape the website", no_tools) is True
    assert query_needs_tools("get the data", no_tools) is True
    assert query_needs_tools("fetch results", no_tools) is True

    assert query_needs_tools("hello world", no_tools) is False
    assert query_needs_tools("what is the weather", no_tools) is False


def test_calc_backoff():
    assert calc_backoff(0) == 1.0
    assert calc_backoff(1) == 2.0
    assert calc_backoff(2) == 4.0
    assert calc_backoff(3) == 8.0

    assert calc_backoff(0, base_delay=2.0) == 2.0
    assert calc_backoff(1, base_delay=2.0) == 4.0
    assert calc_backoff(2, base_delay=2.0) == 8.0
