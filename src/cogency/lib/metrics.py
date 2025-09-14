"""Token counting for streaming agents."""

import tiktoken

from .logger import logger


def count_tokens(text: str, model: str) -> int:
    """Count tokens in text using model-appropriate encoding."""
    if not text:
        return 0

    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except KeyError:
        # Use cl100k_base encoding for unknown models (GPT-4 compatible)
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))


def count_message_tokens(messages: list[dict], model: str) -> int:
    """Count tokens in message array using tiktoken's native message encoding."""
    if not messages:
        return 0

    # Use tiktoken's native message encoding for OpenAI models
    if model.startswith("gpt") or "gpt" in model.lower():
        try:
            enc = tiktoken.encoding_for_model(model)
            return len(enc.encode_messages(messages))
        except (KeyError, AttributeError):
            pass

    # For non-OpenAI models, format messages and count with cl100k_base
    total_text = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        total_text += f"{role}: {content}\n"

    return count_tokens(total_text, model)


class Tokens:
    """Track input/output tokens for streaming agents."""

    def __init__(self, model: str):
        if not model:
            raise ValueError("Model must be specified explicitly. No defaults allowed.")
        self.model = model
        self.input = 0
        self.output = 0

    @classmethod
    def init(cls, llm):
        """Initialize token tracking from LLM."""
        try:
            return cls(getattr(llm, "llm_model", "unknown"))
        except Exception as e:
            logger.warning(f"Token tracking init failed: {e}")
            return None

    def add_input(self, text: str):
        tokens = count_tokens(text, self.model)
        self.input += tokens
        return tokens

    def add_input_messages(self, messages: list[dict]):
        """Add input tokens from message array."""
        tokens = count_message_tokens(messages, self.model)
        self.input += tokens
        return tokens

    def add_output(self, text: str):
        tokens = count_tokens(text, self.model)
        self.output += tokens
        return tokens

    def total(self):
        return self.input + self.output

    def to_step_metrics(self, step_input: int, step_output: int, step_duration: float, total_duration: float) -> dict:
        """Create metrics event with step and total data."""
        return {
            "type": "metrics",
            "step": {
                "input": step_input,
                "output": step_output, 
                "duration": step_duration
            },
            "total": {
                "input": self.input,
                "output": self.output,
                "duration": total_duration
            }
        }
