"""Context generation."""

from typing import Any, Dict, List

from .agent import AgentState


def execution_history(state: AgentState, tools: List[Any]) -> str:
    """State → Rich execution history with full context."""
    if not state.execution.completed_calls:
        return ""

    history_lines = []
    for result in state.execution.completed_calls[-5:]:  # Last 5
        tool_name = result.get("name", "unknown")
        tool_args = result.get("args", {})
        success = result.get("success", False)
        data = result.get("data")
        error = result.get("error")

        # Args summary (first 50 chars)
        args_str = str(tool_args)[:50] if tool_args else ""

        if success:
            # Success: show what was learned
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool and data:
                try:
                    output = tool.format_agent(data)[:150]
                except (KeyError, ValueError, AttributeError):
                    output = "completed"
            else:
                output = "completed"
            history_lines.append(f"✓ {tool_name}({args_str}) → {output}")
        else:
            # Failure: show why it failed
            error_msg = str(error)[:100] if error else "failed"
            history_lines.append(f"✗ {tool_name}({args_str}) → FAILED: {error_msg}")

    return f"EXECUTION HISTORY:\n{chr(10).join(history_lines)}\n\n"


def knowledge_synthesis(state: AgentState) -> str:
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


def readiness_assessment(state: AgentState) -> str:
    """State → Can I respond to the user now?"""

    # Simple heuristics
    has_successful_tools = any(r.get("success", False) for r in state.execution.completed_calls)

    recent_failures = sum(
        1
        for r in state.execution.completed_calls[-3:]
        if not r.get("success", True)  # Count as failure if success is False
    )

    if has_successful_tools and recent_failures == 0:
        readiness = "READY - Have successful results, no recent failures"
    elif recent_failures >= 2:
        readiness = "CONSIDER RESPONDING - Multiple recent failures, may need different approach"
    else:
        readiness = "CONTINUE - Gathering more information"

    return f"RESPONSE READINESS: {readiness}\n\n"


def reasoning_context(state: AgentState, tools: List[Any], mode=None) -> str:
    """Pure function: State → Reasoning Prompt."""

    mode = mode or state.execution.mode
    mode_value = mode.value if hasattr(mode, "value") else str(mode)

    # Situated memory injection
    user_context = state.get_situated_context()

    # Reasoning context
    reasoning_context = state.reasoning.compress_for_context()

    # Tool registry
    tool_registry = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)

    # Rich execution context
    execution_context = execution_history(state, tools)
    knowledge_context = knowledge_synthesis(state)
    readiness_context = readiness_assessment(state)

    # Mode-specific instructions
    if mode_value == "deep":
        instructions = """DEEP MODE: Structured reasoning required
- REFLECT: What have I learned? What worked/failed? What gaps remain?
- ANALYZE: What are the core problems or strategic considerations?  
- STRATEGIZE: What's my multi-step plan? What tools will I use and why?"""
    else:
        instructions = """FAST MODE: Direct execution
- Review context above
- Choose appropriate tools and act efficiently
- ESCALATE to deep mode if task proves complex"""

    # SEC-001: Security-hardened identity
    identity = "You are a helpful AI assistant."

    return f"""{identity}

{user_context}REASONING CONTEXT:
{reasoning_context}

{execution_context}{knowledge_context}{readiness_context}AVAILABLE TOOLS:
{tool_registry}

{instructions}

Iteration {state.execution.iteration}/{state.execution.max_iterations}


Respond with JSON:
{{
    "thinking": "Your reasoning for this step",
    "tool_calls": [
        {{"name": "tool_name", "args": {{"arg": "value"}}}}
    ],
    "workspace_update": {{
        "objective": "refined problem statement if needed",
        "assessment": "current situation analysis", 
        "approach": "strategy being used",
        "observations": ["key insights discovered"]
    }},
    "response": "direct response if ready to answer user",
    "switch_to": "fast|deep",
    "switch_why": "reason for mode switch if switching"
}}"""


def build_context(state: AgentState) -> List[Dict[str, str]]:
    """Build conversation context from agent state.

    Args:
        state: Current agent state

    Returns:
        List of message dictionaries with role and content
    """
    return [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]


# Alias for consistency with imports
conversation_context = build_context
