"""Tokens tests - Cost calculation coverage."""

import pytest

from cogency.lib.tokens import PRICING, Tokens, calculate_cost, count_tokens


def test_count():
    """Token counting works for supported models."""
    # Test with GPT model that tiktoken supports
    tokens = count_tokens("Hello world", "gpt-4o")
    assert tokens > 0
    assert isinstance(tokens, int)


def test_count_empty():
    """Empty text returns 0 tokens."""
    tokens = count_tokens("", "gpt-4o")
    assert tokens == 0


def test_count_unsupported():
    """Unsupported model uses approximation fallback."""
    tokens = count_tokens("test", "unknown-model")
    assert tokens >= 0  # Fallback approximation


def test_calculate_cost():
    """Cost calculation works for supported models."""
    cost = calculate_cost(1000, 500, "gpt-4o")
    expected = (1000 / 1_000_000) * 2.50 + (500 / 1_000_000) * 10.00
    assert cost == expected


def test_calculate_unsupported():
    """Unsupported model raises error."""
    with pytest.raises(ValueError, match="Unsupported model for pricing"):
        calculate_cost(100, 50, "unknown-model")


def test_class():
    """Tokens class tracks input/output correctly."""
    tracker = Tokens("gpt-4o")

    # Add input
    input_tokens = tracker.add_input("Hello world")
    assert input_tokens > 0
    assert tracker.input == input_tokens
    assert tracker.output == 0

    # Add output
    output_tokens = tracker.add_output("Hi there")
    assert output_tokens > 0
    assert tracker.output == output_tokens

    # Total
    assert tracker.total() == input_tokens + output_tokens


def test_cost():
    """Tokens cost calculation works."""
    tracker = Tokens("gpt-4o")
    tracker.input = 1000
    tracker.output = 500

    expected_cost = (1000 / 1_000_000) * 2.50 + (500 / 1_000_000) * 10.00
    assert tracker.cost() == expected_cost


def test_no_model():
    """Tokens requires explicit model."""
    with pytest.raises(ValueError, match="Model must be specified explicitly"):
        Tokens("")


def test_pricing():
    """PRICING dict has expected models."""
    # Core models should be present
    assert "gpt-4o" in PRICING
    assert "gpt-4o-mini" in PRICING
    assert "claude-sonnet-4" in PRICING

    # Pricing format should be consistent
    for _model, pricing in PRICING.items():
        assert "input" in pricing
        assert "output" in pricing
        assert isinstance(pricing["input"], int | float)
        assert isinstance(pricing["output"], int | float)
