"""LLM-based extraction operations."""
import json
from typing import List, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool


async def extract_memory_and_filter_tools(query: str, registry_lite: str, llm: BaseLLM) -> Dict[str, Any]:
    """Single LLM call for both memory extraction and tool filtering using registry lite."""
    prompt = f"""You have input memory and available tools.

MEMORY EXTRACTION:
If this memory contains useful insights, novel info, or actionable patterns worth saving, distill it into a 2-3 sentence summary. Otherwise return null.

TOOL FILTERING:
Only exclude tools you're confident you won't need. Conservative filtering prevents missing needed tools.

# Future: Could add inclusion categories for scale (keep_categories: ["math", "memory", "files"])

Input: "{query}"

Available tools:
{registry_lite}

Return JSON:
{{
  "memory": string | null,
  "reasoning": "Brief explanation of tool filtering decisions",
  "excluded_tools": ["tool1", "tool2", ...]
}}"""

    try:
        response = await llm.invoke([{"role": "user", "content": prompt}])
        result = json.loads(response)
        return {
            "memory_summary": result.get("memory"),
            "reasoning": result.get("reasoning", ""),
            "excluded_tools": result.get("excluded_tools", [])
        }
    except Exception:
        return {"memory_summary": None, "reasoning": "", "excluded_tools": []}