"""Token counting for streaming agents."""

import time

from ..lib.logger import logger

try:  # pragma: no cover - exercised indirectly in tests
    import tiktoken
except Exception:  # pragma: no cover - optional dependency failure
    tiktoken = None  # type: ignore[assignment]

# Cache encoder to avoid rebuilding on every call
_gpt4_encoder = None
_encoder_load_failed = False


def count_tokens(content) -> int:
    """Count tokens using tiktoken when available, otherwise fall back to word count."""

    if not content:
        return 0

    normalized = _normalize(content)

    encoder = _encoder()
    if encoder is not None:
        try:
            return len(encoder.encode(normalized))
        except Exception as exc:  # pragma: no cover - defensive path
            logger.debug("tiktoken encode failed (%s); falling back to word count", exc)

    return _approx_tokens(normalized)


def _normalize(content) -> str:
    """Normalize arbitrary message structures into a single string."""

    if isinstance(content, list):
        return "\n".join(f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in content)
    return str(content)


def _encoder():
    """Lazy-load the GPT-4 encoder, caching failures for offline environments."""

    global _gpt4_encoder, _encoder_load_failed

    if _encoder_load_failed or tiktoken is None:
        return None

    if _gpt4_encoder is None:
        try:
            _gpt4_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:  # pragma: no cover - dependence on external blob
            _encoder_load_failed = True
            logger.debug("Unable to load tiktoken encoder (%s); using word-count fallback", exc)
            return None

    return _gpt4_encoder


def _approx_tokens(text: str) -> int:
    """Heuristic token approximation when tiktoken is unavailable."""

    stripped = text.strip()
    if not stripped:
        return 0
    words = len(stripped.split())
    approx = int((words * 3 + 3) // 4)
    return max(1, approx)


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
