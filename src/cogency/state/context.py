"""Context generation."""

from typing import Any, Dict, List

from .agent import State


def execution_history(state: State, tools: List[Any]) -> str:
    """State → Rich execution history with full context."""
    if not state.execution.completed_calls:
        return ""

    history_lines = []
    tool_patterns = {}  # Track tool+args patterns for repetition detection
    successful_results = {}

    for result in state.execution.completed_calls[-5:]:  # Last 5
        tool_name = result.get("name", "unknown")
        tool_args = result.get("args", {})
        success = result.get("success", False)
        data = result.get("data")
        error = result.get("error")

        # Track pattern-based usage (tool + args signature)
        pattern_key = f"{tool_name}:{str(tool_args)[:30]}"
        tool_patterns[pattern_key] = tool_patterns.get(pattern_key, 0) + 1

        # Store successful results for context
        if success and data:
            successful_results[tool_name] = str(data)

        # Args summary (first 50 chars)
        args_str = str(tool_args)[:50] if tool_args else ""

        if success:
            # Success: show what was learned
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool and data:
                try:
                    output = tool.format_agent(data)
                except (KeyError, ValueError, AttributeError):
                    output = "completed"
            else:
                output = "completed"

            # Add pattern-based repetition warning
            count = tool_patterns[pattern_key]
            repeat_warning = f" [USED {count}x]" if count > 1 else ""
            history_lines.append(f"✓ {tool_name}({args_str}) → {output}{repeat_warning}")
        else:
            # Failure: provide full diagnostic context
            error_str = str(error) if error else "Unknown error"
            if "not found" in error_str.lower():
                error_analysis = (
                    f"FAILED: Resource not found - verify path exists. Error: {error_str}"
                )
            else:
                error_analysis = f"FAILED: {error_str}"
            count = tool_patterns[pattern_key]
            repeat_warning = f" [USED {count}x]" if count > 1 else ""
            history_lines.append(f"✗ {tool_name}({args_str}) → {error_analysis}{repeat_warning}")

    # Pattern-based repetition warnings with actionable context
    repetition_warnings = []
    for pattern_key, count in tool_patterns.items():
        if count >= 2:
            tool_name = pattern_key.split(":")[0]
            if tool_name in successful_results:
                repetition_warnings.append(
                    f"⚠️ {tool_name} already succeeded with similar args - result: {successful_results[tool_name]}"
                )
            elif count >= 3:
                repetition_warnings.append(
                    f"⚠️ {tool_name} failed {count} times with similar args - try different approach"
                )

    # Show successful results for context
    success_context = []
    if successful_results:
        success_context.append("RECENT SUCCESSFUL RESULTS:")
        for tool_name, output in list(successful_results.items())[-3:]:
            success_context.append(f"- {tool_name}: {output}")

    history_section = f"EXECUTION HISTORY:\n{chr(10).join(history_lines)}\n"
    if repetition_warnings:
        history_section += f"\nREPETITION WARNINGS:\n{chr(10).join(repetition_warnings)}\n"
    if success_context:
        history_section += f"\n{chr(10).join(success_context)}\n"

    return history_section + "\n"


def knowledge_synthesis(state: State) -> str:
    """State → Synthesized knowledge from all tool results."""
    knowledge = []

    # Extract insights from successful tool calls
    for result in state.execution.completed_calls:
        if result.get("success", False):
            tool_name = result["name"]
            data = result.get("data")

            # Tool-specific knowledge extraction
            if tool_name == "files" and isinstance(data, str):
                knowledge.append(f"File content: {len(data)} chars loaded")
            elif tool_name == "search" and isinstance(data, list):
                knowledge.append(f"Found {len(data)} search results")
            elif tool_name == "shell" and isinstance(data, dict) and "stdout" in data:
                output = data["stdout"].strip()
                if output:
                    knowledge.append(f"Command output: {output[:100]}")

    if not knowledge:
        return ""

    return f"KNOWLEDGE GATHERED:\n{chr(10).join(f'- {k}' for k in knowledge[-5:])}\n\n"


def readiness_assessment(state: State) -> str:
    """State → Factual summary for LLM decision-making."""

    # Just provide facts, let LLM decide
    successful_calls = [r for r in state.execution.completed_calls if r.get("success", False)]
    failed_calls = [r for r in state.execution.completed_calls if not r.get("success", True)]
    recent_failures = len(
        [r for r in state.execution.completed_calls[-3:] if not r.get("success", True)]
    )

    facts = [
        f"Successful tool calls: {len(successful_calls)}",
        f"Failed tool calls: {len(failed_calls)}",
        f"Recent failures (last 3): {recent_failures}",
    ]

    if successful_calls:
        recent_success = successful_calls[-1]
        facts.append(f"Last success: {recent_success.get('name', 'unknown')} tool")

    # Add readiness recommendation based on execution state
    readiness_line = ""
    if successful_calls and recent_failures == 0:
        readiness_line = "RESPONSE READINESS: READY - Have successful results, no recent failures"
    elif recent_failures >= 2:
        readiness_line = "RESPONSE READINESS: CONSIDER RESPONDING - Multiple recent failures"
    else:
        readiness_line = "RESPONSE READINESS: CONTINUE - Gathering more information"

    facts_section = f"EXECUTION FACTS:\n{chr(10).join(f'- {fact}' for fact in facts)}\n\n"
    return facts_section + readiness_line + "\n\n"


def build_context(state: State) -> List[Dict[str, str]]:
    """Build conversation context from agent state.

    Args:
        state: Current agent state

    Returns:
        List of message dictionaries with role and content
    """
    return [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]
