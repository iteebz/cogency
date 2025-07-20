"""LLM-based extraction operations."""
from typing import List, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.utils.json import extract_json


async def extract_memory_and_filter_tools(query: str, registry_lite: str, llm: BaseLLM) -> Dict[str, Any]:
    """Single LLM call for memory extraction, tool filtering, complexity analysis, and routing decision."""
    prompt = f"""You have input query and available tools.

MEMORY EXTRACTION:
If this query contains useful insights, novel info, or actionable patterns worth saving, distill it into a 2-3 sentence summary. Otherwise return null.

DYNAMIC TAGGING:
If extracting memory, generate 2-5 relevant tags for categorization and search. Focus on:
- Technical domains (ai, web, data, security, etc.)
- Action types (problem, solution, learning, insight, etc.) 
- Context (priority, performance, etc.)

ROUTING DECISION:
Can this query be answered directly with your knowledge? Consider:
- Math calculations (2+2, basic arithmetic)
- General knowledge (definitions, explanations, facts)
- Conversational responses (greetings, thanks)
If YES: set "bypass_react" to true
If NO (needs external data, tools, search): set "bypass_react" to false

COMPLEXITY ANALYSIS:
Analyze query complexity for reasoning depth (0.1-1.0). Consider:
- Length and structure complexity
- Multi-step reasoning requirements  
- Domain expertise needed
- Ambiguity and context requirements
- Tool coordination complexity

TOOL FILTERING:
Only exclude tools you're absolutely certain you won't need. When in doubt, include the tool. Be extremely conservative - it's better to include tools that might be useful than to exclude tools that could be needed.

Input: "{query}"

Available tools:
{registry_lite}

Return JSON:
{{
  "memory": string | null,
  "tags": ["tag1", "tag2", ...] | null,
  "memory_type": "fact" | "episodic" | "experience" | "context",
  "complexity": 0.1-1.0,
  "bypass_react": true | false,
  "reasoning": "Brief explanation of routing, complexity and tool filtering decisions", 
  "excluded_tools": ["tool1", "tool2", ...]
}}"""

    response = await llm.invoke([{"role": "user", "content": prompt}])
    
    fallback = {"memory_summary": None, "tags": [], "memory_type": "fact", "complexity": 0.5, "bypass_react": False, "reasoning": "", "excluded_tools": []}
    result = extract_json(response, fallback)
    
    return {
        "memory_summary": result.get("memory"),
        "tags": result.get("tags", []) if result.get("memory") else [],
        "memory_type": result.get("memory_type", "fact"),
        "complexity": result.get("complexity", 0.5),
        "bypass_react": result.get("bypass_react", False),
        "reasoning": result.get("reasoning", ""),
        "excluded_tools": result.get("excluded_tools", [])
    }