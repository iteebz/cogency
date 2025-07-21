"""In-scope planning capabilities for deep mode."""

from typing import Any, Dict, List, Optional


def planning_prompt() -> str:
    """Get the planning section for deep mode prompts."""
    return """📋 PLANNING PHASE:
Based on my reflection, what's my next strategy? What specific approach should I take?
- Break down the problem if complex
- Identify key information needed
- Plan tool usage sequence
- Consider potential obstacles"""


def extract_planning_strategy(llm_response: str) -> Optional[Dict[str, Any]]:
    """Extract planning strategy from LLM response.

    Returns:
        Dict with planning details or None if not found
    """
    try:
        import json

        # Try to extract JSON from response
        start = llm_response.find("{")
        end = llm_response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = llm_response[start:end]
            data = json.loads(json_str)

            planning_info = {
                "strategy": data.get("strategy"),
                "planning": data.get("planning"),
                "approach": data.get("approach"),
                "tool_sequence": data.get("tool_sequence", []),
                "expected_obstacles": data.get("expected_obstacles", []),
            }

            return planning_info if any(planning_info.values()) else None

    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract planning from text
    if "PLANNING:" in llm_response or "📋" in llm_response:
        lines = llm_response.split("\n")
        planning_lines = []
        in_planning = False

        for line in lines:
            if any(marker in line for marker in ["PLANNING", "📋"]):
                in_planning = True
                continue
            elif any(marker in line for marker in ["EXECUTION", "🎯", "REFLECTION", "🤔"]):
                in_planning = False
            elif in_planning and line.strip():
                planning_lines.append(line.strip())

        if planning_lines:
            return {
                "strategy": "text_extracted",
                "planning": " ".join(planning_lines),
                "approach": None,
                "tool_sequence": [],
                "expected_obstacles": [],
            }

    return None


def validate_planning_quality(planning_info: Optional[Dict[str, Any]]) -> bool:
    """Validate if the planning is of sufficient quality.

    Args:
        planning_info: Planning information extracted from response

    Returns:
        True if planning meets quality standards
    """
    if not planning_info:
        return False

    # Check if planning has substantial content
    planning_text = planning_info.get("planning", "")
    if not planning_text or len(planning_text.strip()) < 10:
        return False

    # Basic quality indicators
    quality_indicators = [
        "because",
        "then",
        "first",
        "next",
        "if",
        "approach",
        "strategy",
        "plan",
        "need",
        "search",
        "analyze",
    ]

    text_lower = planning_text.lower()
    indicator_count = sum(1 for indicator in quality_indicators if indicator in text_lower)

    return indicator_count >= 2


def create_multi_step_plan(
    query: str, available_tools: List[str], current_context: Optional[str] = None
) -> Dict[str, Any]:
    """Create a multi-step plan for complex queries.

    Args:
        query: The user's query
        available_tools: List of available tool names
        current_context: Current conversation context

    Returns:
        Multi-step plan structure
    """
    # Simple heuristic-based planning
    plan_steps = []

    # Analyze query for planning indicators
    query_lower = query.lower()

    # Search-first queries
    if any(word in query_lower for word in ["find", "search", "look up", "what is", "who is"]):
        if "search" in available_tools:
            plan_steps.append(
                {
                    "step": 1,
                    "action": "search",
                    "reasoning": "Gather initial information",
                    "tool": "search",
                }
            )

    # Analysis queries need multiple steps
    if any(word in query_lower for word in ["analyze", "compare", "contrast", "synthesize"]):
        plan_steps.append(
            {
                "step": len(plan_steps) + 1,
                "action": "gather_information",
                "reasoning": "Collect data for analysis",
                "tool": "search" if "search" in available_tools else "any",
            }
        )
        plan_steps.append(
            {
                "step": len(plan_steps) + 1,
                "action": "analyze",
                "reasoning": "Process and analyze collected information",
                "tool": "reasoning",
            }
        )

    return {
        "total_steps": len(plan_steps),
        "steps": plan_steps,
        "complexity": "high" if len(plan_steps) > 2 else "medium",
        "estimated_iterations": min(len(plan_steps) + 1, 5),
    }


def format_plan_for_display(plan: Dict[str, Any]) -> str:
    """Format a plan for human-readable display.

    Args:
        plan: Plan dictionary

    Returns:
        Formatted plan string
    """
    if not plan or not plan.get("steps"):
        return "Simple direct approach"

    lines = [f"📋 MULTI-STEP PLAN ({plan['total_steps']} steps):"]

    for step in plan["steps"]:
        lines.append(f"  {step['step']}. {step['action']} - {step['reasoning']}")

    return "\n".join(lines)
