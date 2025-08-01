"""Early routing - direct responses for simple queries."""

from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.steps.respond.utils import format_response
from cogency.tools import Tool
from cogency.utils import is_simple_query


class Route:
    """Early routing when tools can't help with query."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def check_early_return(
        self, query: str, selected_tools: List[Tool], identity: Optional[str] = None
    ) -> Optional[str]:
        """Check if query can be answered directly without ReAct."""
        query_str = query if isinstance(query, str) else str(query)

        # Early return conditions:
        # 1. Simple query with no tools selected
        # 2. Explicit no-tool selection by LLM
        if not selected_tools and is_simple_query(query_str):
            return await self._direct_response(query_str, identity)

        return None

    async def _direct_response(self, query: str, identity: Optional[str] = None) -> str:
        """Generate direct LLM response for simple queries."""
        prompt = f"Answer this simple question directly: {query}"
        result = await self.llm.run([{"role": "user", "content": prompt}])
        response = unwrap(result)
        return format_response(response.strip(), identity=identity)
