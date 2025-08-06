"""Core triage functions - consolidated business logic."""

from dataclasses import dataclass
from typing import List, Optional

from resilient_result import unwrap

from cogency.events import emit
from cogency.providers import LLM
from cogency.security import secure_semantic
from cogency.tools import Tool
from cogency.tools.registry import build_tool_descriptions
from cogency.utils.parsing import _parse_json

from .prompt import build_triage_prompt


@dataclass
class SelectionResult:
    selected_tools: List[str]
    reasoning: str


@dataclass
class TriageResult:
    """Result of unified triage step."""

    # Early return
    direct_response: Optional[str] = None

    # Tool selection
    selected_tools: List[str] = None

    # Mode classification
    mode: str = "fast"

    # Reasoning explanation
    reasoning: str = ""

    def __post_init__(self):
        if self.selected_tools is None:
            self.selected_tools = []


def filter_tools(tools: List[Tool], selected_names: List[str]) -> List[Tool]:
    """Filter tools based on selection."""
    if not selected_names:
        return []

    selected_set = set(selected_names)
    filtered = [tool for tool in tools if tool.name in selected_set]
    return [tool for tool in filtered if tool.name != "memorize"]


async def check_early_return(llm: LLM, query: str, selected_tools: List[Tool]) -> Optional[str]:
    """Check if query can be answered directly without ReAct."""
    query_str = query if isinstance(query, str) else str(query)

    # Use LLM to determine if this query needs tools
    return await _early_check(llm, query_str, selected_tools)


async def _early_check(llm: LLM, query: str, available_tools: List[Tool]) -> Optional[str]:
    """Use LLM to intelligently determine if query needs full pipeline."""
    tool_names = [tool.name for tool in available_tools] if available_tools else []

    # Quick classification prompt
    prompt = f"""Query: "{query}"
Available tools: {tool_names}

Can this query be answered with ONLY the information I currently have? Answer with:
- "DIRECT: [answer]" if I have all the specific data/context needed
- "TOOLS" if I need to gather information, execute commands, or access external data

Examples:
- "What does pwd do?" → "DIRECT: Shows current directory"
- "Use pwd to show current directory" → "TOOLS"
- "What is 5+5?" → "DIRECT: 10"
- "Hello, who are you?" → "DIRECT: I'm an AI assistant"
- "What's the weather in NYC?" → "TOOLS"
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

    registry_lite = build_tool_descriptions(available_tools)

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


async def notify_tool_selection(filtered_tools: List[Tool], total_tools: int) -> None:
    """Send appropriate notifications about tool selection."""
    if not filtered_tools:
        return

    selected_count = len(filtered_tools)

    if selected_count < total_tools:
        emit(
            "triage",
            state="filtered",
            selected_tools=selected_count,
            total_tools=total_tools,
        )
    elif selected_count == 1:
        emit("triage", state="direct", tool_count=1)
    else:
        emit("triage", state="react", tool_count=selected_count)


async def triage_prompt(
    llm: LLM, query: str, available_tools: List[Tool], user_context: str = "", identity: str = None
) -> TriageResult:
    """Single LLM call to handle all triage tasks."""
    emit("triage", level="debug", state="analyzing", tool_count=len(available_tools))

    # Build tool registry for context
    registry_lite = (
        build_tool_descriptions(available_tools) if available_tools else "No tools available"
    )

    prompt = build_triage_prompt(query, registry_lite, user_context, identity)

    emit("triage", level="debug", state="llm_call")
    result = await llm.run([{"role": "user", "content": prompt}])
    response = unwrap(result)
    parsed = unwrap(_parse_json(response))

    # Handle case where LLM returns array instead of object
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}
    elif not isinstance(parsed, dict):
        parsed = {}

    # Extract and process security assessment from unified response
    emit("triage", level="debug", state="security_check")
    security_data = parsed.get("security_assessment", {})
    security_result = secure_semantic(security_data)

    if not security_result.safe:
        emit("triage", level="debug", state="security_violation")
        return TriageResult(
            direct_response=security_result.message
            or "Security violation: Request contains unsafe content"
        )

    # Extract response fields
    selected_tools = parsed.get("selected_tools", [])
    direct_response = parsed.get("direct_response")

    # Emit completion events
    if direct_response:
        emit("triage", level="debug", state="direct_response")
    elif selected_tools:
        emit("triage", level="debug", state="tools_selected", selected_tools=len(selected_tools))
    else:
        emit("triage", level="debug", state="no_tools")

    return TriageResult(
        direct_response=direct_response,
        selected_tools=selected_tools,
        mode=parsed.get("mode", "fast"),
        reasoning=parsed.get("reasoning", ""),
    )
