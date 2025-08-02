"""Early routing - direct responses for simple queries."""

from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.tools import Tool
from cogency.utils import is_simple_query


class Route:
    """Early routing when tools can't help with query."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def check_early_return(self, query: str, selected_tools: List[Tool]) -> Optional[str]:
        """Check if query can be answered directly without ReAct."""
        query_str = query if isinstance(query, str) else str(query)

        # Early return conditions:
        # 1. Simple query with no tools selected
        if not selected_tools and is_simple_query(query_str):
            return await self._direct_response(query_str)

        # 2. Use LLM to determine if this is a simple query that doesn't need tools
        # This replaces the overfitted math-specific patterns with general intelligence
        return await self._intelligent_early_check(query_str, selected_tools)

    async def _intelligent_early_check(
        self, query: str, available_tools: List[Tool]
    ) -> Optional[str]:
        """Use LLM to intelligently determine if query needs full pipeline."""
        tool_names = [tool.name for tool in available_tools] if available_tools else []

        # Quick classification prompt
        classification_prompt = f"""Query: "{query}"
Available tools: {tool_names}

Can this query be answered directly without using any tools? Answer with:
- "DIRECT: [your answer]" if it can be answered directly
- "TOOLS" if it requires tools or complex reasoning

Examples:
- "What is 5+5?" → "DIRECT: 10"
- "Hello, who are you?" → "DIRECT: I'm an AI assistant"
- "What's the weather?" → "TOOLS"
- "Search for Python tutorials" → "TOOLS"
"""

        result = await self.llm.run([{"role": "user", "content": classification_prompt}])
        from resilient_result import unwrap

        response = unwrap(result).strip()

        # Parse response
        if response.startswith("DIRECT:"):
            return response[7:].strip()

        return None

    def _is_simple_math(self, query: str) -> bool:
        """Check if query is simple math that can be answered directly."""
        import re

        # Enhanced math patterns to catch more variations
        math_patterns = [
            # Basic arithmetic questions
            r"what\s+is\s+\d+\s*[+\-*/×÷]\s*\d+",  # "what is 2+2", "what is 5 * 3"
            r"what.*\d+\s*[+\-*/×÷]\s*\d+",  # "what's 7*8"
            # Direct arithmetic expressions
            r"^\d+\s*[+\-*/×÷]\s*\d+\s*[=?]*\s*$",  # "2+2", "7 * 8", "5-3?"
            # Word-based math
            r"add\s+\d+\s+(and|to)\s+\d+",  # "add 5 and 3", "add 2 to 7"
            r"subtract\s+\d+\s+from\s+\d+",  # "subtract 3 from 10"
            r"multiply\s+\d+\s+(by|and)\s+\d+",  # "multiply 4 by 5", "multiply 6 and 9"
            r"divide\s+\d+\s+by\s+\d+",  # "divide 15 by 3"
            # Calculate variations
            r"calculate\s+\d+\s*[+\-*/×÷]\s*\d+",  # "calculate 5*5"
            r"compute\s+\d+\s*[+\-*/×÷]\s*\d+",  # "compute 8/2"
            # Equation formats
            r"\d+\s*[+\-*/×÷]\s*\d+\s*=\s*\?",  # "5 + 5 = ?"
            r".*equals.*\d+\s*[+\-*/×÷]\s*\d+",  # "what equals 3*4"
        ]

        query_lower = query.lower().strip()
        return any(re.search(pattern, query_lower) for pattern in math_patterns)

    async def _direct_response(self, query: str) -> str:
        """Generate direct LLM response for simple queries."""
        prompt = f"Answer this simple question directly: {query}"
        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        return response.strip()
