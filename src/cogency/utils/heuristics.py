"""
Pragmatic heuristics for stability and control flow.

PRINCIPLE: Smart reasoning (LLM), dumb tools (heuristics for plumbing only)

ALLOWED:
- Network retry logic
- Loop detection
- Basic sanity checks
- Control flow guards

FORBIDDEN:
- Content quality scoring
- Semantic analysis
- "Smart" query parsing
- Any attempt to understand meaning with if/else

All heuristics must justify their existence as structural guardrails, not semantic understanding.
"""

from typing import Dict, List


def is_simple_query(query: str) -> bool:
    """Check if query is simple enough to suggest fast mode.

    Structural heuristic: Single/double word queries without complex punctuation
    likely don't need deep reasoning cycles.
    """
    words = query.split()
    return len(words) <= 2 and not any(char in query for char in "?!")


def needs_network_retry(errors: List[Dict]) -> bool:
    """Check if errors indicate network issues that warrant retry.

    Structural heuristic: Detect transient network failures that benefit from
    exponential backoff rather than reasoning about the failure.
    """
    if not errors:
        return False

    network_errors = [
        "timeout",
        "rate limit",
        "connection",
        "network",
        "429",
        "503",
        "502",
    ]

    return any(
        any(net_err in str(error.get("error", "")).lower() for net_err in network_errors)
        for error in errors
    )


def query_needs_tools(query: str, available_tools: List) -> bool:
    """Check if query needs tools but none are available.

    Structural heuristic: Prevent ReAct dead-ends when user explicitly asks
    for tool-requiring operations but no tools are selected.
    """
    if available_tools:  # Tools are available
        return False

    # Keywords that clearly indicate tool usage needed
    tool_keywords = ["search", "find", "look up", "scrape", "get", "fetch"]
    needs_tools = any(keyword in query.lower() for keyword in tool_keywords)

    return needs_tools


def calc_backoff(retry_count: int, base_delay: float = 1.0) -> float:
    """Calculate exponential backoff delay for network retries.

    Structural heuristic: Standard exponential backoff to avoid hammering
    rate-limited or failing services.
    """
    return base_delay * (2**retry_count)
