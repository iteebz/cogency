"""Token counting for streaming agents."""

import time

import tiktoken


def count_tokens(content) -> int:
    """Count tokens using tiktoken - gpt-4 approximation for all providers."""
    if not content:
        return 0

    # Convert messages to text if needed
    if isinstance(content, list):
        content = "\n".join(f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in content)

    # Use gpt-4 tokenizer for all providers
    enc = tiktoken.encoding_for_model("gpt-4")
    return len(enc.encode(content))


class Metrics:
    """Track comprehensive metrics for streaming agents."""

    def __init__(self, model: str):
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0
        self.step_input_tokens = 0
        self.step_output_tokens = 0
        self.step_start_time = None
        self.task_start_time = None

    @classmethod
    def init(cls, model: str):
        """Initialize metrics tracking."""
        metrics = cls(model)
        metrics.task_start_time = time.time()
        return metrics

    def start_step(self):
        """Start timing a new step and reset step counters."""
        self.step_start_time = time.time()
        self.step_input_tokens = 0
        self.step_output_tokens = 0
        return self.step_start_time

    def add_input(self, text):
        tokens = count_tokens(text)
        self.input_tokens += tokens
        self.step_input_tokens += tokens
        return tokens

    def add_output(self, text: str):
        tokens = count_tokens(text)
        self.output_tokens += tokens
        self.step_output_tokens += tokens
        return tokens

    def total_tokens(self):
        return self.input_tokens + self.output_tokens

    def event(self) -> dict:
        """Create clean metrics event."""
        now = time.time()
        return {
            "type": "metrics",
            "step": {
                "input": self.step_input_tokens,
                "output": self.step_output_tokens,
                "duration": now - self.step_start_time,
            },
            "total": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "duration": now - self.task_start_time,
            },
        }
