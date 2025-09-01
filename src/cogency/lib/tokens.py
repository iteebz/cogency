"""Token counting and cost analysis."""

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Production cost optimization - streaming consciousness TCO analysis with actual rates
PRICING = {
    # OpenAI Standard Models
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
    "o1-mini": {"input": 1.10, "output": 4.40},
    "o3-mini": {"input": 1.10, "output": 4.40},
    # OpenAI Realtime Models
    "gpt-4o-realtime-preview": {"input": 5.00, "output": 20.00},
    "gpt-4o-mini-realtime-preview": {"input": 0.60, "output": 2.40},
    # Gemini Models
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
    "models/gemini-2.5-flash-live-preview": {"input": 0.50, "output": 2.00},
    # Anthropic Claude
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00},
    # Embeddings
    "text-embedding-3-small": {"input": 0.01, "output": 0.00},
    "text-embedding-3-large": {"input": 0.065, "output": 0.00},
    "gemini-embedding-001": {"input": 0.15, "output": 0.00},
}


def count_tokens(text: str, model: str) -> int:
    if not text:
        return 0

    if not TIKTOKEN_AVAILABLE:
        # Fallback approximation: ~4 chars per token
        return len(text) // 4

    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except KeyError:
        # Fallback approximation for unknown models
        return len(text) // 4


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    if model not in PRICING:
        raise ValueError(
            f"Unsupported model for pricing: {model}. Add to PRICING dict with actual rates."
        )

    pricing = PRICING[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


class Tokens:
    """Track input/output tokens with cost analysis."""

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
        except Exception:
            return None

    def add_input(self, text: str):
        tokens = count_tokens(text, self.model)
        self.input += tokens
        return tokens

    def add_output(self, text: str):
        tokens = count_tokens(text, self.model)
        self.output += tokens
        cost = self.cost()
        print(f"+{tokens} | Total: {self.total()} | ${cost:.4f}")
        return tokens

    def total(self):
        return self.input + self.output

    def cost(self) -> float:
        return calculate_cost(self.input, self.output, self.model)

    def compare_streaming_cost(self, stream_model: str) -> dict:
        batch_cost = self.cost()
        stream_cost = calculate_cost(self.input, self.output, stream_model)

        return {
            "batch_model": self.model,
            "batch_cost": batch_cost,
            "stream_model": stream_model,
            "stream_cost": stream_cost,
            "premium": stream_cost / batch_cost if batch_cost > 0 else 0,
            "savings": batch_cost - stream_cost,
        }
