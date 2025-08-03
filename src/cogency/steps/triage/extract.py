"""Memory extraction - async, focused, composable."""

from dataclasses import dataclass
from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.utils.parsing import _parse_json


@dataclass
class MemoryResult:
    content: Optional[str]
    tags: List[str]
    memory_type: str = "fact"


class Extract:
    """Memory extraction using embedding similarity."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def extract(self, query: str) -> MemoryResult:
        """Extract user facts worth persisting."""
        prompt = f"""Extract memorable user facts from this query:

Query: "{query}"

JSON Response:
{{
  "memory": "extracted user fact relevant for persistence" | null,
  "tags": ["topical", "categories"] | [],
  "memory_type": "fact"
}}

EXTRACTION RULES:
- Extract factual user statements (goals, context, identity, preferences)
- Ignore questions, commands, or temporary context
- Return null if no memorable facts present
- Tags should be interpretive categories for later retrieval

Examples:
- "I'm building a React app" → "User mentioned building a React app"
- "What is 2+2?" → null
- "My name is John" → "User's name is John"
"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        parsed = unwrap(_parse_json(response))

        return MemoryResult(
            content=parsed.get("memory"),
            tags=parsed.get("tags", []),
            memory_type=parsed.get("memory_type", "fact"),
        )

    async def save_memory(self, memory_result: MemoryResult, memory_service, notifier) -> None:
        """Save extracted memory if present."""
        if not memory_result.content or not memory_service:
            return

        # Truncate for notification display
        content = memory_result.content
        if len(content) > 60:
            break_point = content.rfind(" ", 40, 60)
            if break_point == -1:
                break_point = 60
            display_content = f"{content[:break_point]}..."
        else:
            display_content = content

        await notifier("triage", state="memory_saved", content_preview=display_content)
        await memory_service.remember(content, human=True)
