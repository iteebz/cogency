"""Tool selection - intelligent filtering based on query needs."""

from dataclasses import dataclass
from typing import List

from resilient_result import unwrap

from cogency.services import LLM
from cogency.tools import Tool, build_registry
from cogency.utils import parse_json


@dataclass
class SelectionResult:
    selected_tools: List[str]
    reasoning: str


class ToolSelector:
    """Intelligently selects relevant tools for query execution."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def select(self, query: str, available_tools: List[Tool]) -> SelectionResult:
        """Select tools needed for query execution."""
        if not available_tools:
            return SelectionResult(selected_tools=[], reasoning="No tools available")

        registry_lite = build_registry(available_tools, lite=True)

        prompt = f"""Select tools needed for this query:

Query: "{query}"

Available Tools:
{registry_lite}

JSON Response:
{{
  "selected_tools": ["tool1", "tool2"] | [],
  "reasoning": "brief justification of tool choices"
}}

SELECTION RULES:
- Select only tools directly needed for execution
- Empty list means no tools needed (direct LLM response)
- Consider query intent and tool capabilities
- Prefer minimal tool sets that accomplish the goal"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        parsed = unwrap(parse_json(response))

        return SelectionResult(
            selected_tools=parsed.get("selected_tools", []), reasoning=parsed.get("reasoning", "")
        )

    def filter_tools(self, tools: List[Tool], selected_names: List[str]) -> List[Tool]:
        """Filter tools based on selection."""
        if not selected_names:
            return []

        selected_set = set(selected_names)
        filtered = [tool for tool in tools if tool.name in selected_set]

        # Remove memorize tool - memory extraction is handled separately
        return [tool for tool in filtered if tool.name != "memorize"]
