"""Triage step - routing, memory extraction, tool filtering.

The triage step handles initial request processing:
- Routing decisions for request type
- Memory extraction and context building
- Tool selection and filtering

Internal implementation uses Flow pipeline for robust processing.
"""

from dataclasses import dataclass
from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.security import assess
from cogency.state import AgentState
from cogency.tools import Tool
from cogency.tools.registry import build_registry
from cogency.utils.parsing import _parse_json

from .flow import Flow
from .prompt import build_triage_prompt


@dataclass
class TriageResult:
    """Result of unified triage step."""

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

    def __post_init__(self):
        if self.memory_tags is None:
            self.memory_tags = []
        if self.selected_tools is None:
            self.selected_tools = []


class Triage:
    """Single LLM call for all triage tasks."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def triage(self, query: str, available_tools: List[Tool]) -> TriageResult:
        """Single LLM call to handle all triage tasks."""

        # Build tool registry for context
        registry_lite = (
            build_registry(available_tools, lite=True) if available_tools else "No tools available"
        )

        prompt = build_triage_prompt(query, registry_lite)

        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        parsed = unwrap(_parse_json(response))

        # Handle case where LLM returns array instead of object
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        elif not isinstance(parsed, dict):
            parsed = {}

        # Pass LLM security assessment to the single security function
        security_section = parsed.get("security_assessment", {}) or {}
        security_result = await assess(query, {"security_assessment": security_section})

        if not security_result.safe:  # SEC-001: Prompt injection protection
            return TriageResult(
                direct_response="Security violation: Request contains unsafe content"
            )

        # Extract memory section safely
        memory_section = parsed.get("memory", {}) or {}

        return TriageResult(
            direct_response=parsed.get("direct_response"),
            memory_content=memory_section.get("content"),
            memory_tags=memory_section.get("tags", []),
            selected_tools=parsed.get("selected_tools", []),
            mode=parsed.get("mode", "fast"),
            reasoning=parsed.get("reasoning", ""),
        )


async def triage(
    state: AgentState,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Triage: routing decisions, memory extraction, tool selection."""
    pipeline = Flow(llm, tools, memory)
    return await pipeline.process(state, notifier)
