"""Eval execution context management."""


class AgentRobustContext:
    """Context manager to inject robust=True into Agent instantiation during evals."""

    def __init__(self, robust: bool):
        self.robust = robust
        self._original_agent_init = None

    def __enter__(self):
        if not self.robust:
            return self

        # Import here to avoid circular imports
        from cogency import Agent

        # Store original init
        self._original_agent_init = Agent.__init__

        # Create wrapper that injects robust=True
        def _wrapped_init(agent_self, *args, **kwargs):
            # Inject robust=True if not explicitly set
            if "robust" not in kwargs:
                kwargs["robust"] = True
            return self._original_agent_init(agent_self, *args, **kwargs)

        # Replace Agent.__init__ temporarily
        Agent.__init__ = _wrapped_init
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.robust and self._original_agent_init:
            # Restore original init
            from cogency import Agent

            Agent.__init__ = self._original_agent_init
