"""Stream observation decorator - clean separation of concerns."""

import functools
import time

from .tokens import Tokens


def observe(agent):
    """Decorator to observe agent stream execution with metrics collection."""
    model = agent.config.llm.llm_model

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create metrics collector
            tokens = Tokens(model)
            start_time = time.time()

            # Execute the function and observe its stream
            async for event in func(*args, **kwargs):
                # Track tokens from event content
                if isinstance(event, dict) and "content" in event:
                    content = event["content"]
                    if content and isinstance(content, str):
                        tokens.add_output(content)
                yield event

            # Store final metrics on function object
            wrapper.metrics = {
                "input_tokens": tokens.input,
                "output_tokens": tokens.output,
                "duration": time.time() - start_time,
            }

        return wrapper

    return decorator


class Observer:
    """Stream wrapper for observation without decorator."""

    def __init__(self, stream, model: str, input_messages: list[dict] = None):
        self.stream = stream
        self.tokens = Tokens(model)
        self.start_time = time.time()
        self.duration = 0.0

        # Track input tokens from messages provided at stream start
        if input_messages:
            self.tokens.add_input_messages(input_messages)

    async def __aiter__(self):
        """Stream events while tracking metrics."""
        async for event in self.stream:
            # Track output tokens from event content
            if isinstance(event, dict) and "content" in event:
                content = event["content"]
                if content and isinstance(content, str):
                    self.tokens.add_output(content)
            yield event

        # Finalize timing
        self.duration = time.time() - self.start_time

    def get_metrics(self) -> dict:
        """Get final metrics after stream completion."""
        return {
            "input_tokens": self.tokens.input,
            "output_tokens": self.tokens.output,
            "duration": self.duration,
        }
