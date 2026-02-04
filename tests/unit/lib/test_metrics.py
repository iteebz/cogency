from unittest import mock

from cogency.lib import metrics
from cogency.lib.metrics import Metrics, _approx_tokens, count_tokens


def test_word_count_approximation():
    # Basic word counting
    assert count_tokens("Hello world") == 2
    assert count_tokens("") == 0
    assert count_tokens("Single") == 1

    # Consistent relative measurement
    short_text = "Hello"
    long_text = "Hello world this is much longer"
    assert count_tokens(long_text) > count_tokens(short_text)


def test_message_token_counting():
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello world"},
    ]

    tokens = count_tokens(messages)
    assert tokens > 0

    # Empty messages
    assert count_tokens([]) == 0
    assert count_tokens(None) == 0

    # Larger context should have more tokens
    large_messages = [
        {"role": "system", "content": "You are a very helpful assistant" * 10},
        {"role": "user", "content": "Please help me with this complex task"},
    ]
    assert count_tokens(large_messages) > count_tokens(messages)


def test_metrics_initialization():
    metrics = Metrics.init("gpt-4")

    assert metrics.input_tokens == 0
    assert metrics.output_tokens == 0
    assert metrics.step_input_tokens == 0
    assert metrics.step_output_tokens == 0
    assert metrics.task_start_time is not None


def test_step_tracking():
    metrics = Metrics.init("gpt-4")

    # Step 1
    metrics.start_step()
    step1_input = metrics.add_input("Large context message")
    step1_output = metrics.add_output("Response")

    assert metrics.step_input_tokens == step1_input
    assert metrics.step_output_tokens == step1_output

    # Step 2 - counters should reset
    metrics.start_step()
    step2_input = metrics.add_input("Small update")
    step2_output = metrics.add_output("OK")

    # Step counters reset
    assert metrics.step_input_tokens == step2_input
    assert metrics.step_output_tokens == step2_output

    # Total counters accumulate
    assert metrics.input_tokens == step1_input + step2_input
    assert metrics.output_tokens == step1_output + step2_output


def test_efficiency_measurement():
    # Simulate replay mode - context grows each step
    replay_metrics = Metrics.init("gpt-4")

    # Step 1: Full context
    replay_metrics.start_step()
    replay_step1_input = replay_metrics.add_input(
        [
            {"role": "system", "content": "Long system prompt " * 50},
            {"role": "user", "content": "What is 2+2?"},
        ]
    )
    replay_metrics.add_output('{"name": "calculate", "args": {}}')

    # Step 2: Full context + history
    replay_metrics.start_step()
    replay_step2_input = replay_metrics.add_input(
        [
            {"role": "system", "content": "Long system prompt " * 50},
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": '{"name": "calculate", "args": {}}'},
            {"role": "system", "content": "Result: 4"},
        ]
    )
    replay_metrics.add_output("The answer is 4")

    # Simulate resume mode - incremental context
    resume_metrics = Metrics.init("gpt-4")

    # Step 1: Same as replay
    resume_metrics.start_step()
    resume_step1_input = resume_metrics.add_input(
        [
            {"role": "system", "content": "Long system prompt " * 50},
            {"role": "user", "content": "What is 2+2?"},
        ]
    )
    resume_metrics.add_output('{"name": "calculate", "args": {}}')

    # Step 2: Only incremental context (tool result)
    resume_metrics.start_step()
    resume_step2_input = resume_metrics.add_input("Result: 4")  # Just tool result
    resume_metrics.add_output("The answer is 4")

    # Verify efficiency measurement
    assert replay_step1_input == resume_step1_input  # Same initial context
    assert replay_step2_input > resume_step2_input  # Resume is more efficient

    # Resume should use significantly fewer input tokens in step 2
    efficiency_ratio = replay_step2_input / resume_step2_input
    assert efficiency_ratio > 10  # Resume is 10x+ more efficient


def test_metrics_event_generation():
    metrics = Metrics.init("gpt-4")

    # Simulate a complete step
    metrics.start_step()
    metrics.add_input("Input text")
    metrics.add_output("Output text")

    # Generate event with no parameters
    event = metrics.event()

    assert event["type"] == "metric"
    assert "step" in event
    assert "total" in event

    # Step metrics
    assert event["step"]["input"] > 0
    assert event["step"]["output"] > 0
    assert event["step"]["duration"] >= 0

    # Total metrics
    assert event["total"]["input"] > 0
    assert event["total"]["output"] > 0
    assert event["total"]["duration"] >= 0


def test_llm_content_tracking():
    metrics = Metrics.init("gpt-4")
    metrics.start_step()

    # Simulate different LLM content types
    think_tokens = metrics.add_output("I need to analyze this problem")
    call_tokens = metrics.add_output('{"name": "file_search", "args": {"pattern": "*.py"}}')
    respond_tokens = metrics.add_output("Found 5 Python files in the project")

    # All content types should be counted
    assert think_tokens > 0
    assert call_tokens > 0
    assert respond_tokens > 0

    # Total should include all types
    expected_total = think_tokens + call_tokens + respond_tokens
    assert metrics.output_tokens == expected_total
    assert metrics.step_output_tokens == expected_total


def test_total_tokens():
    m = Metrics.init("gpt-4")
    m.add_input("input text")
    m.add_output("output text")
    assert m.total_tokens() == m.input_tokens + m.output_tokens


def test_approx_tokens_empty():
    assert _approx_tokens("") == 0
    assert _approx_tokens("   ") == 0


def test_approx_tokens_single_word():
    assert _approx_tokens("hello") >= 1


def test_approx_tokens_multiple_words():
    result = _approx_tokens("hello world this is a test")
    assert result > 0
    # Formula: (words * 3 + 3) // 4, min 1
    # 6 words -> (6 * 3 + 3) // 4 = 21 // 4 = 5
    assert result == 5


def test_count_tokens_without_tiktoken():
    """count_tokens falls back to _approx_tokens when tiktoken unavailable."""
    with mock.patch.object(metrics, "tiktoken", None):
        tokens = count_tokens("hello world")
        # Word-based approximation
        assert tokens > 0


def test_count_tokens_tiktoken_none_check():
    """Encoder returns None when tiktoken is None."""
    original = metrics.tiktoken
    original_encoder = metrics._gpt4_encoder
    original_failed = metrics._encoder_load_failed
    try:
        metrics.tiktoken = None
        metrics._gpt4_encoder = None
        metrics._encoder_load_failed = False
        result = count_tokens("test")
        assert result > 0
    finally:
        metrics.tiktoken = original
        metrics._gpt4_encoder = original_encoder
        metrics._encoder_load_failed = original_failed
