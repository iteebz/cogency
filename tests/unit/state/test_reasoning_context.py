"""Reasoning tests - Structured cognition."""

from cogency.state.reasoning import Reasoning


def test_create():
    """Test creating a Reasoning instance."""
    context = Reasoning(goal="test goal")
    assert context.goal == "test goal"


def test_defaults():
    """Test that default values are properly set."""
    context = Reasoning()

    assert context.goal == ""
    assert context.facts == {}
    assert context.strategy == ""
    assert context.insights == []
    assert context.thoughts == []


def test_learn():
    """Test adding insights with bounded growth."""
    context = Reasoning()

    # Add unique insights
    context.learn("First insight")
    context.learn("Second insight")

    assert len(context.insights) == 2
    assert "First insight" in context.insights
    assert "Second insight" in context.insights

    # Duplicate insights are ignored
    context.learn("First insight")
    assert len(context.insights) == 2

    # Empty insights are ignored
    context.learn("")
    context.learn("   ")
    assert len(context.insights) == 2

    # Test bounded growth (max 10)
    for i in range(15):
        context.learn(f"Insight {i}")

    assert len(context.insights) <= 10


def test_update_facts():
    """Test updating structured knowledge."""
    context = Reasoning()

    # Add facts
    context.update_facts("key1", "value1")
    context.update_facts("key2", {"nested": "value"})

    assert context.facts["key1"] == "value1"
    assert context.facts["key2"] == {"nested": "value"}

    # Update existing fact
    context.update_facts("key1", "updated_value")
    assert context.facts["key1"] == "updated_value"

    # Empty keys are ignored
    context.update_facts("", "ignored")
    context.update_facts("   ", "ignored")
    assert "" not in context.facts

    # Test bounded growth (max 20)
    for i in range(25):
        context.update_facts(f"key_{i}", f"value_{i}")

    assert len(context.facts) <= 20


def test_record_thinking():
    """Test recording reasoning steps."""
    context = Reasoning()

    # Record thoughts
    context.record_thinking("First thought", [{"tool": "test"}])
    context.record_thinking("Second thought", [])

    assert len(context.thoughts) == 2
    assert context.thoughts[0]["thinking"] == "First thought"
    assert context.thoughts[0]["tool_calls"] == [{"tool": "test"}]
    assert context.thoughts[1]["thinking"] == "Second thought"
    assert "timestamp" in context.thoughts[0]

    # Test bounded growth (max 5)
    for i in range(10):
        context.record_thinking(f"Thought {i}", [])

    assert len(context.thoughts) <= 5


def testcompress_for_context():
    """Test intelligent compression for LLM context."""
    context = Reasoning(goal="Test goal", strategy="Test strategy")

    # Add some data
    context.learn("Test insight")
    context.update_facts("test_key", "test_value")
    context.record_thinking("Test thinking", [])

    compressed = context.compress_for_context()

    assert "GOAL: Test goal" in compressed
    assert "STRATEGY: Test strategy" in compressed
    assert "FACTS: test_key: test_value" in compressed
    assert "INSIGHTS: Test insight" in compressed
    assert "LAST THINKING: Test thinking" in compressed

    # Test max tokens limit
    short = context.compress_for_context(max_tokens=50)
    assert len(short) <= 50
