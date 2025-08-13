"""Agent resilience - always-on with smart error classification."""

import os

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


def configurable_resilience(enabled_env: str = "COGENCY_RESILIENCE_ENABLED"):
    """Environment-controlled resilience - always on by default."""
    enabled = os.getenv(enabled_env, "true").lower() == "true"

    def decorator(func=None, **kwargs):
        if not enabled:
            return func if func else lambda f: f

        # Apply smart resilience
        base_resilient = resilient(handler=smart_handler, **kwargs)
        return base_resilient(func) if func else base_resilient

    return decorator


# Canonical agent resilience decorator - always on by default
resilience = configurable_resilience()
