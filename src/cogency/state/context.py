"""Context generation."""

from typing import Any, Dict, List

from .agent import AgentState


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

    # Recent results with formatted output
    max_recent = 3
    recent_results = (
        state.execution.completed_calls[-max_recent:] if state.execution.completed_calls else []
    )
    results_context = ""
    if recent_results:
        results_parts = []
        for result in recent_results:
            name = result.get("name", "unknown")
            result_obj = result.get("result")
            success = result_obj.success if result_obj and hasattr(result_obj, "success") else False
            status = "✓" if success else "✗"

            # Use tool's agent template for formatted output
            formatted_output = ""
            if success and result_obj and hasattr(result_obj, "data") and result_obj.data:
                tool = next((t for t in tools if t.name == name), None)
                if tool:
                    try:
                        formatted_output = f" → {tool.format_agent(result_obj.data)}"
                    except (KeyError, ValueError, AttributeError):
                        # Graceful fallback if tool template fails
                        formatted_output = f" → {name} completed"

            results_parts.append(f"{status} {name}{formatted_output}")
        results_context = f"RECENT RESULTS:\n{'\n'.join(results_parts)}\n\n"

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

    return f"""{user_context}REASONING CONTEXT:
{reasoning_context}

{results_context}AVAILABLE TOOLS:
{tool_registry}

{instructions}

Iteration {state.execution.iteration}/{state.execution.max_iterations}

Respond with JSON:
{{
    "thinking": "Your reasoning for this step",
    "tool_calls": [
        {{"name": "tool_name", "args": {{"arg": "value"}}}}
    ],
    "context_updates": {{
        "goal": "refined goal if needed",
        "strategy": "current approach", 
        "insights": ["new insight if discovered"]
    }},
    "response": "direct response if ready to answer user",
    "switch_mode": "fast|deep"
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
