"""LLM-based extraction operations."""
import json
from typing import List, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool


async def extract_memory_and_filter_tools(query: str, registry_lite: str, llm: BaseLLM) -> Dict[str, Any]:
    """Single LLM call for memory extraction, tag generation, and tool filtering."""
    prompt = f"""You have input query and available tools.

MEMORY EXTRACTION:
If this query contains useful insights, novel info, or actionable patterns worth saving, distill it into a 2-3 sentence summary. Otherwise return null.

DYNAMIC TAGGING:
If extracting memory, generate 2-5 relevant tags for categorization and search. Focus on:
- Technical domains (ai, web, data, security, etc.)
- Action types (problem, solution, learning, insight, etc.) 
- Context (priority, performance, etc.)

TOOL FILTERING:
Only exclude tools you're confident you won't need. Conservative filtering prevents missing needed tools.

Input: "{query}"

Available tools:
{registry_lite}

Return JSON:
{{
  "memory": string | null,
  "tags": ["tag1", "tag2", ...] | null,
  "memory_type": "fact" | "episodic" | "experience" | "context",
  "reasoning": "Brief explanation of tool filtering decisions", 
  "excluded_tools": ["tool1", "tool2", ...]
}}"""

    try:
        response = await llm.invoke([{"role": "user", "content": prompt}])
        result = json.loads(response)
        return {
            "memory_summary": result.get("memory"),
            "tags": result.get("tags", []) if result.get("memory") else [],
            "memory_type": result.get("memory_type", "fact"),
            "reasoning": result.get("reasoning", ""),
            "excluded_tools": result.get("excluded_tools", [])
        }
    except Exception:
        return {"memory_summary": None, "tags": [], "memory_type": "fact", "reasoning": "", "excluded_tools": []}