"""Tool workflow sequences evaluation."""

import os

from cogency.tools.files import Files
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ..eval import Eval, EvalResult


class ToolChains(Eval):
    """Test agent's ability to chain multiple tools in sequence."""

    name = "tool_chains"
    description = "Test tool workflow sequences and data flow"

    async def run(self) -> EvalResult:
        agent = self.create_agent(
            "chain_tester",
            tools=[Files(), Search(), Shell()],
            max_iterations=15,
        )

        query = """Create a file called 'search_results.txt', search for 'Python async programming best practices', 
        write the top 3 results to the file, then use shell to count the lines in the file."""

        result = await agent.run_async(query)

        # Check if agent executed the chain properly
        response_lower = result.lower()

        # Look for evidence of each step
        created_file = any(word in response_lower for word in ["created", "wrote", "file"])
        performed_search = any(word in response_lower for word in ["search", "found", "results"])
        used_shell = any(word in response_lower for word in ["lines", "wc", "count"])

        # Check if file actually exists and has content
        file_exists = os.path.exists("search_results.txt")
        has_content = False
        
        if file_exists:
            try:
                with open("search_results.txt", "r") as f:
                    content = f.read()
                    has_content = bool(content and content.strip())
                # Clean up
                os.remove("search_results.txt")
            except Exception:
                has_content = False

        # Success requires all chain steps
        passed = created_file and performed_search and used_shell and file_exists and has_content
        score = 1.0 if passed else sum([created_file, performed_search, used_shell, file_exists, has_content]) / 5.0

        agent_logs = agent.logs() if hasattr(agent, "logs") else []

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,
            traces=[{
                "query": query,
                "response": result,
                "created_file": created_file,
                "performed_search": performed_search,
                "used_shell": used_shell,
                "file_exists": file_exists,
                "has_content": has_content,
                "logs": agent_logs,
            }],
            metadata={
                "created_file": created_file,
                "performed_search": performed_search,
                "used_shell": used_shell,
                "file_exists": file_exists,
                "has_content": has_content,
            },
        )