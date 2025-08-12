"""Thinking output formatting for console display."""


def is_deep_thinking(content: str) -> bool:
    """Detect if content represents deep vs quick thinking."""
    deep_keywords = {
        "analyze",
        "consider",
        "strategy",
        "approach",
        "architecture",
        "pattern",
        "design",
        "structure",
        "planning",
        "reviewing",
        "examining",
        "evaluating",
        "determining",
        "understanding",
    }

    return any(keyword in content.lower() for keyword in deep_keywords) or len(content) > 150


def is_repetitive_thinking(content: str, recent_thinking: list[str]) -> bool:
    """Check if thinking content is repetitive."""
    if len(recent_thinking) == 0:
        return False

    # Check similarity with recent thoughts
    return any(_similarity_ratio(content, recent) > 0.8 for recent in recent_thinking[-3:])


def format_thinking(content: str) -> str:
    """Format thinking content with appropriate symbol."""
    symbol = "*" if is_deep_thinking(content) else "◦"
    return f"{symbol} {content}"


def _similarity_ratio(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    if not text1 or not text2:
        return 0.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0
