"""Core triage functions - consolidated business logic."""

from dataclasses import dataclass
from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.security import assess
from cogency.tools import Tool
from cogency.tools.registry import build_registry
from cogency.utils.heuristics import is_simple_query
from cogency.utils.parsing import _parse_json

from .prompt import build_triage_prompt


@dataclass
class MemoryResult:
    content: Optional[str]
    tags: List[str]
    memory_type: str = "fact"


@dataclass
class SelectionResult:
    selected_tools: List[str]
    reasoning: str


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


def filter_tools(tools: List[Tool], selected_names: List[str]) -> List[Tool]:
    """Filter tools based on selection."""
    if not selected_names:
        return []

    selected_set = set(selected_names)
    filtered = [tool for tool in tools if tool.name in selected_set]
    return [tool for tool in filtered if tool.name != "memorize"]


async def extract_memory(llm: LLM, query: str) -> MemoryResult:
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

    result = await llm.run([{"role": "user", "content": prompt}])
    response = unwrap(result)
    parsed = unwrap(_parse_json(response))

    return MemoryResult(
        content=parsed.get("memory"),
        tags=parsed.get("tags", []),
        memory_type=parsed.get("memory_type", "fact"),
    )


async def save_memory(memory_result: MemoryResult, memory_service, notifier) -> None:
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


async def check_early_return(llm: LLM, query: str, selected_tools: List[Tool]) -> Optional[str]:
    """Check if query can be answered directly without ReAct."""
    query_str = query if isinstance(query, str) else str(query)

    # Early return conditions:
    # 1. Simple query with no tools selected
    if not selected_tools and is_simple_query(query_str):
        return await _direct_response(llm, query_str)

    # 2. Use LLM to determine if this is a simple query that doesn't need tools
    return await _early_check(llm, query_str, selected_tools)


async def _early_check(llm: LLM, query: str, available_tools: List[Tool]) -> Optional[str]:
    """Use LLM to intelligently determine if query needs full pipeline."""
    tool_names = [tool.name for tool in available_tools] if available_tools else []

    # Quick classification prompt
    prompt = f"""Query: "{query}"
Available tools: {tool_names}

Can this query be answered directly without using any tools? Answer with:
- "DIRECT: [your answer]" if it can be answered directly
- "TOOLS" if it requires tools or complex reasoning

Examples:
- "What is 5+5?" → "DIRECT: 10"
- "Hello, who are you?" → "DIRECT: I'm an AI assistant"
- "What's the weather?" → "TOOLS"
- "Search for Python tutorials" → "TOOLS"
"""

    result = await llm.run([{"role": "user", "content": prompt}])
    response = unwrap(result).strip()

    # Parse response
    if response.startswith("DIRECT:"):
        return response[7:].strip()

    return None


async def _direct_response(llm: LLM, query: str) -> str:
    """Generate direct LLM response."""
    prompt = f"Answer this simple question directly: {query}"
    result = await llm.run([{"role": "user", "content": prompt}])
    response = unwrap(result)
    return response.strip()


async def select_tools(llm: LLM, query: str, available_tools: List[Tool]) -> SelectionResult:
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

    result = await llm.run([{"role": "user", "content": prompt}])
    response = unwrap(result)
    parsed = unwrap(_parse_json(response))

    return SelectionResult(
        selected_tools=parsed.get("selected_tools", []), reasoning=parsed.get("reasoning", "")
    )


async def notify_tool_selection(notifier, filtered_tools: List[Tool], total_tools: int) -> None:
    """Send appropriate notifications about tool selection."""
    if not filtered_tools:
        return

    selected_count = len(filtered_tools)

    if selected_count < total_tools:
        await notifier(
            "triage",
            state="filtered",
            selected_tools=selected_count,
            total_tools=total_tools,
        )
    elif selected_count == 1:
        await notifier("triage", state="direct", tool_count=1)
    else:
        await notifier("triage", state="react", tool_count=selected_count)


async def unified_triage(llm: LLM, query: str, available_tools: List[Tool]) -> TriageResult:
    """Single LLM call to handle all triage tasks."""

    # Build tool registry for context
    registry_lite = (
        build_registry(available_tools, lite=True) if available_tools else "No tools available"
    )

    prompt = build_triage_prompt(query, registry_lite)

    result = await llm.run([{"role": "user", "content": prompt}])
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
        return TriageResult(direct_response="Security violation: Request contains unsafe content")

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
