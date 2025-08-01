"""Query complexity classification - fast vs deep reasoning modes."""

from dataclasses import dataclass

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.utils import is_simple_query, parse_json


@dataclass
class ClassificationResult:
    mode: str
    reasoning: str


class Context:
    """Query context classification and mode requirements."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def build(self, query: str) -> ClassificationResult:
        """Determine if query needs fast or deep reasoning."""
        query_str = query if isinstance(query, str) else str(query)

        # Heuristic override for obviously simple queries
        if is_simple_query(query_str):
            return ClassificationResult(
                mode="fast", reasoning="Simple query detected by heuristics"
            )

        # LLM classification for complex cases
        prompt = f"""Classify this query's complexity for reasoning mode selection:

Query: "{query}"

JSON Response:
{{
  "mode": "fast" | "deep",
  "reasoning": "brief justification"
}}

CLASSIFICATION CRITERIA:
- FAST: Single factual lookup, basic calculation, direct command, simple question
- DEEP: Multiple sources needed, comparison/synthesis, creative generation, coding tasks"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        parsed = unwrap(parse_json(response))

        return ClassificationResult(
            mode=parsed.get("mode", "fast"), reasoning=parsed.get("reasoning", "")
        )
