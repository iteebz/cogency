"""Agent resilience - smart error classification."""

from resilient_result import resilient

# Import ValidationError if available, fallback otherwise
try:
    from pydantic import ValidationError
except ImportError:

    class ValidationError(Exception):
        pass


def smart_handler(error):
    """Expose bugs immediately, retry transient failures.

    Returns:
        False: Stop retrying - this is a code bug
        None: Continue retrying - this is transient
    """
    # Code bugs = stop immediately
    if isinstance(
        error,
        (
            ValidationError,
            TypeError,
            AttributeError,
            KeyError,
            ImportError,
            NameError,
            IndentationError,
            SyntaxError,
        ),
    ):
        return False

    # API/network issues = retry gracefully
    return None


# Canonical agent resilience decorator
resilience = resilient(handler=smart_handler)
