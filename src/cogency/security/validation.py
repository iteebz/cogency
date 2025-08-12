"""Input validation and security checks."""

MAX_QUERY_LENGTH = 10000


def validate_query(query: str) -> str | None:
    """Validate user query input.

    Args:
        query: User query string to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not query or not query.strip():
        return "⚠️ Empty query not allowed"

    if len(query) > MAX_QUERY_LENGTH:
        return f"⚠️ Query too long (max {MAX_QUERY_LENGTH:,} characters)"

    return None
