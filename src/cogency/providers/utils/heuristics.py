"""
Pragmatic heuristics for stability and control flow.

PRINCIPLE: Smart reasoning (LLM), dumb tools (heuristics for plumbing only)

ALLOWED:
- Network retry logic
- Basic sanity checks
- Control flow guards

FORBIDDEN:
- Content quality scoring
- Semantic analysis
- "Smart" query parsing
- Any attempt to understand meaning with if/else

All heuristics must justify their existence as structural guardrails, not semantic understanding.
"""


def needs_network_retry(errors: list[dict]) -> bool:
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


def calc_backoff(retry_count: int, base_delay: float = 1.0) -> float:
    """Calculate exponential backoff delay for network retries.

    Structural heuristic: Standard exponential backoff to avoid hammering
    rate-limited or failing services.
    """
    return base_delay * (2**retry_count)
