import pytest

from cogency.lib.tokens import PRICING, Tokens, calculate_cost, count_tokens


def test_token_counting_and_cost_calculation():
    """Token counting and cost calculation with model support and fallbacks."""

    # Token counting behavior
    assert count_tokens("Hello world", "gpt-4o") > 0
    assert count_tokens("", "gpt-4o") == 0
    assert count_tokens("test", "unknown-model") >= 0  # Fallback approximation

    # Direct cost calculation
    cost = calculate_cost(1000, 500, "gpt-4o")
    expected = (1000 / 1_000_000) * 2.50 + (500 / 1_000_000) * 10.00
    assert cost == expected

    # Unsupported model raises error for pricing
    with pytest.raises(ValueError, match="Unsupported model for pricing"):
        calculate_cost(100, 50, "unknown-model")

    # Tokens class tracking and calculations
    tracker = Tokens("gpt-4o")

    input_tokens = tracker.add_input("Hello world")
    output_tokens = tracker.add_output("Hi there")

    assert tracker.input == input_tokens > 0
    assert tracker.output == output_tokens > 0
    assert tracker.total() == input_tokens + output_tokens

    # Direct cost calculation from tracker
    tracker.input = 1000
    tracker.output = 500
    assert tracker.cost() == expected

    # Pricing data structure validation
    core_models = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4"]
    for model in core_models:
        assert model in PRICING
        assert "input" in PRICING[model]
        assert "output" in PRICING[model]
        assert isinstance(PRICING[model]["input"], int | float)
        assert isinstance(PRICING[model]["output"], int | float)

    # Model validation
    with pytest.raises(ValueError, match="Model must be specified explicitly"):
        Tokens("")
