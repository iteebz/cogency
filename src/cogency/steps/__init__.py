"""Clean step imports - zero ceremony."""

from .act import act
from .prepare import prepare
from .reason import reason
from .respond import respond

__all__ = [
    "act",
    "prepare",
    "reason",
    "respond",
    "setup_steps",
]


def setup_steps(llm, tools, memory, identity, output_schema, config=None):
    """Production-hardened step composition with elegant zero-ceremony API."""
    from functools import partial

    from resilient_result import Retry, resilient

    from cogency.observe import counter, timer

    # Import production capabilities
    from cogency.robust import checkpoint

    def _compose_step(
        step_func, step_name, checkpoint_name=None, needs_resilience=False, **bind_args
    ):
        """Compose production capabilities into step function."""
        # Start with bound function
        bound_func = partial(step_func, **bind_args)

        # Add production hardening based on config
        if config:
            # Observability - always add if enabled
            if getattr(config, "observe", None):

                def observed_func(*args, **kwargs):
                    counter(f"{step_name}.executions", 1.0, {"step": step_name})
                    with timer(f"{step_name}.duration", {"step": step_name}):
                        return bound_func(*args, **kwargs)

                bound_func = observed_func

            # Resilience - add retry logic for steps that need it
            if getattr(config, "robust", None) and needs_resilience:
                if step_name == "act":
                    retry_policy = Retry.db()  # Database/API-style retry for tool execution
                else:
                    retry_policy = Retry.api()  # Standard API retry
                bound_func = resilient(retry=retry_policy)(bound_func)

            # Checkpointing - for long-running or interruptible steps
            if getattr(config, "persist", None) and checkpoint_name:
                bound_func = checkpoint(checkpoint_name, interruptible=True)(bound_func)

        return bound_func

    return {
        "prepare": _compose_step(
            prepare, "prepare", llm=llm, tools=tools, memory=memory, identity=identity
        ),
        "reason": _compose_step(
            reason,
            "reason",
            checkpoint_name="reasoning",
            needs_resilience=True,
            llm=llm,
            tools=tools,
            memory=memory,
            identity=identity,
        ),
        "act": _compose_step(
            act, "act", checkpoint_name="tool_execution", needs_resilience=True, tools=tools
        ),
        "respond": _compose_step(
            respond,
            "respond",
            llm=llm,
            tools=tools,
            memory=memory,
            identity=identity,
            output_schema=output_schema,
        ),
    }
