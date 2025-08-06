"""Minimal step composition - toggleable resilience and checkpointing."""

from resilient_result import Retry, resilient

from cogency.robust import checkpoint


def resilient_step(retry_policy: Retry):
    """Add resilience to step function."""

    def decorator(func):
        return resilient(retry=retry_policy)(func)

    return decorator


def checkpointed_step(name: str):
    """Add checkpointing to step function."""

    def decorator(func):
        return checkpoint(name, interruptible=True)(func)

    return decorator


def compose_step(step_func, config=None, checkpoint_name=None, retry_policy=None):
    """Compose step with optional resilience and checkpointing."""
    composed = step_func

    if config and getattr(config, "robust", None) and retry_policy:
        composed = resilient_step(retry_policy)(composed)

    if config and getattr(config, "persist", None) and checkpoint_name:
        composed = checkpointed_step(checkpoint_name)(composed)

    return composed


__all__ = ["resilient_step", "checkpointed_step", "compose_step"]
