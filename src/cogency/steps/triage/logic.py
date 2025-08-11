"""Core triage functions - consolidated business logic."""

from dataclasses import dataclass
from typing import Optional

from resilient_result import unwrap

from cogency.events import emit
from cogency.providers import Provider
from cogency.security import secure_semantic
from cogency.tools import Tool
from cogency.tools.registry import build_tool_descriptions
from cogency.utils.parsing import _parse_json

from .prompt import build_triage_prompt


@dataclass
class TriageResult:
    """Result of unified triage step."""

    # Early return
    direct_response: Optional[str] = None

    # Tool selection
    selected_tools: list[str] = None

    # Mode classification
    mode: str = "fast"

    # Reasoning explanation
    reasoning: str = ""

    # Memory semantic flags
    memory_flags: dict = None

    def __post_init__(self):
        if self.selected_tools is None:
            self.selected_tools = []
        if self.memory_flags is None:
            self.memory_flags = {}


def _queue_memory_updates(query: str, memory_flags: dict) -> None:
    """Queue async memory updates based on semantic triggers."""
    if memory_flags.get("situated"):
        emit(
            "memory", level="debug", action="queue_situated", reason=memory_flags.get("reason", "")
        )
        # Set flag that situate core can check
        # This will be picked up by the main execution loop

    if memory_flags.get("archival"):
        emit(
            "memory", level="debug", action="queue_archival", reason=memory_flags.get("reason", "")
        )
        # TODO: Implement archival memory queueing when archival system is ready


def filter_tools(tools: list[Tool], selected_names: list[str]) -> list[Tool]:
    """Filter tools based on selection."""
    if not selected_names:
        return []

    selected_set = set(selected_names)
    filtered = [tool for tool in tools if tool.name in selected_set]
    return [tool for tool in filtered if tool.name != "memorize"]


async def notify_tool_selection(filtered_tools: list[Tool], total_tools: int) -> None:
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
    llm: Provider,
    query: str,
    available_tools: list[Tool],
    user_context: str = "",
    identity: str = None,
) -> TriageResult:
    """Single LLM call to handle all triage tasks."""
    emit("triage", level="debug", state="analyzing", tool_count=len(available_tools))

    # Build tool registry for context
    registry_lite = (
        build_tool_descriptions(available_tools) if available_tools else "No tools available"
    )

    prompt = build_triage_prompt(query, registry_lite, user_context, identity)

    emit("triage", level="debug", state="provider_call")
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
    memory_flags_raw = parsed.get("memory_flags", {})

    # Handle memory_flags - ensure it's a dict, not a string
    if isinstance(memory_flags_raw, str):
        # LLM returned string instead of dict - default to empty dict
        memory_flags = {}
        emit("triage", level="debug", state="memory_flags_string_fallback", raw=memory_flags_raw)
    elif isinstance(memory_flags_raw, dict):
        memory_flags = memory_flags_raw
    else:
        memory_flags = {}

    # Queue async memory updates if semantic triggers detected
    if memory_flags.get("situated") or memory_flags.get("archival"):
        _queue_memory_updates(query, memory_flags)

    # Emit completion events
    if direct_response:
        emit("triage", level="debug", state="direct_response")
    elif selected_tools:
        emit("triage", level="debug", state="tools_selected", selected_tools=len(selected_tools))
    else:
        emit("triage", level="debug", state="no_tools")

    if memory_flags.get("situated") or memory_flags.get("archival"):
        emit("triage", level="debug", state="memory_flagged", flags=memory_flags)

    return TriageResult(
        direct_response=direct_response,
        selected_tools=selected_tools,
        mode=parsed.get("mode", "fast"),
        reasoning=parsed.get("reasoning", ""),
        memory_flags=memory_flags,
    )
