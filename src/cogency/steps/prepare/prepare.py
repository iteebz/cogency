"""Unified prepare step - single LLM call for all preparation tasks."""

from dataclasses import dataclass
from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.tools import Tool
from cogency.tools.registry import build_registry
from cogency.utils.parsing import _parse_json


@dataclass
class PrepareResult:
    """Result of unified preparation step."""

    # Early return
    direct_response: Optional[str] = None

    # Memory extraction
    memory_content: Optional[str] = None
    memory_tags: List[str] = None

    # Tool selection
    selected_tools: List[str] = None

    # Mode classification
    mode: str = "fast"

    # Reasoning explanation
    reasoning: str = ""

    # Reasoning
    reasoning = ""

    def __post_init__(self):
        if self.memory_tags is None:
            self.memory_tags = []
        if self.selected_tools is None:
            self.selected_tools = []


class Prepare:
    """Single LLM call for all preparation tasks."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def prepare(self, query: str, available_tools: List[Tool]) -> PrepareResult:
        """Single LLM call to handle all preparation tasks."""

        # Build tool registry for context
        registry_lite = (
            build_registry(available_tools, lite=True) if available_tools else "No tools available"
        )

        prompt = f"""Analyze this query and provide a comprehensive preparation plan:

Query: "{query}"

Available Tools:
{registry_lite}

JSON Response:
{{
  "direct_response": "complete answer if query can be answered directly without tools" | null,
  "memory": {{
    "content": "extracted user fact worth persisting" | null,
    "tags": ["topical", "categories"] | [],
    "type": "fact"
  }},
  "selected_tools": ["tool1", "tool2"] | [],
  "mode": "fast" | "deep",
  "reasoning": "brief explanation of decisions"
}}

DECISION RULES:

1. DIRECT RESPONSE:
   - Simple math: "What is 5+5?" → "10"
   - Basic facts: "What color is the sky?" → "Blue"
   - Greetings: "Hello" → "Hello! How can I help?"
   - Identity: "Who are you?" → "I'm an AI assistant"
   - If direct response provided, ignore tools/mode

2. MEMORY EXTRACTION:
   - Extract factual user statements (goals, context, identity, preferences)
   - Ignore questions, commands, or temporary context
   - Examples: "I'm building a React app" → extract, "What is 2+2?" → null

3. TOOL SELECTION:
   - Select only tools directly needed for execution
   - Empty list means no tools needed (direct LLM response)
   - Consider query intent and tool capabilities

4. MODE CLASSIFICATION:
   - FAST: Single factual lookup, basic calculation, direct command
   - DEEP: Multiple sources needed, comparison/synthesis, creative generation

EXAMPLES:
Query: "What is 15 + 7?"
→ {{"direct_response": "22", "memory": {{"content": null, "tags": []}}, "selected_tools": [], "mode": "fast", "reasoning": "Simple arithmetic"}}

Query: "Search for Python tutorials"  
→ {{"direct_response": null, "memory": {{"content": null, "tags": []}}, "selected_tools": ["search"], "mode": "fast", "reasoning": "Direct search query"}}

Query: "I'm learning machine learning and need help with neural networks"
→ {{"direct_response": null, "memory": {{"content": "User is learning machine learning", "tags": ["education", "ML"]}}, "selected_tools": ["search"], "mode": "deep", "reasoning": "Educational query requiring comprehensive response"}}
"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        parsed = unwrap(_parse_json(response))

        # Handle case where LLM returns array instead of object
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        elif not isinstance(parsed, dict):
            parsed = {}

        # Extract memory section safely
        memory_section = parsed.get("memory", {}) or {}

        return PrepareResult(
            direct_response=parsed.get("direct_response"),
            memory_content=memory_section.get("content"),
            memory_tags=memory_section.get("tags", []),
            selected_tools=parsed.get("selected_tools", []),
            mode=parsed.get("mode", "fast"),
            reasoning=parsed.get("reasoning", ""),
        )
