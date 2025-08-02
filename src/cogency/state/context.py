"""Pure functional context generation - no methods in state classes."""

from typing import Any, Dict, List

from .agent import AgentState


def build_reasoning_prompt(state: AgentState, tools: List[Any], mode: str = None) -> str:
    """Pure function: State → Reasoning Prompt."""
    mode = mode or state.execution.mode

    # Situated memory injection
    user_context = state.get_situated_context()

    # Reasoning context
    reasoning_context = state.reasoning.compress_for_context()

    # Tool registry
    tool_registry = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)

    # Recent results
    recent_results = state.execution.completed_calls[-3:] if state.execution.completed_calls else []
    results_context = ""
    if recent_results:
        results_parts = []
        for result in recent_results:
            name = result.get("name", "unknown")
            status = "✓" if result.get("success", False) else "✗"
            results_parts.append(f"{status} {name}")
        results_context = "RECENT RESULTS:\n" + "\n".join(results_parts) + "\n\n"

    # Mode-specific instructions
    if mode == "deep":
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
        {{"name": "tool_name", "args": {{"param": "value"}}}}
    ],
    "context_updates": {{
        "goal": "refined goal if needed",
        "strategy": "current approach", 
        "insights": ["new insight if discovered"]
    }},
    "response": "direct response if ready to answer user",
    "switch_mode": "fast|deep"
}}"""


def build_conversation_context(state: AgentState) -> List[Dict[str, str]]:
    """Pure function: State → LLM Messages."""
    return [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]
