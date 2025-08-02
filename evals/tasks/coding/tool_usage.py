"""Tool usage evaluation."""

from cogency import Agent
from cogency.tools.search import Search

from ...core import Eval, EvalResult


class ToolUsage(Eval):
    """Test agent's ability to use tools effectively."""

    name = "tool_usage"
    description = "Test tool integration and usage patterns"

    async def run(self) -> EvalResult:
        agent = Agent("tool_tester", tools=[Search()], mode="fast", memory=False)

        query = "Search for information about Python list comprehensions and summarize the key benefits."
        result = await agent.run(query)

        # Check if agent actually used search and provided meaningful response
        response_lower = result.lower()
        has_search_indicators = any(
            word in response_lower for word in ["search", "found", "according", "based on"]
        )
        has_list_comp_content = any(
            word in response_lower for word in ["comprehension", "syntax", "efficient", "readable"]
        )

        if has_search_indicators and has_list_comp_content:
            score = 1.0
            passed = True
        elif has_list_comp_content:
            score = 0.7
            passed = False
        else:
            score = 0.0
            passed = False

        metadata = {
            "query": query,
            "response": result,
            "has_search_indicators": has_search_indicators,
            "has_list_comp_content": has_list_comp_content,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,  # Will be set by base class
            expected="Tool usage with relevant content",
            actual=f"Score: {score:.1%}",
            metadata=metadata,
        )
