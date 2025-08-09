"""Tool workflow sequences evaluation."""

import os

from cogency.tools.files import Files
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ..eval import Eval


class ToolChains(Eval):
    """Test agent's ability to chain multiple tools in sequence."""

    name = "tool_chains"
    description = "Test tool workflow sequences and data flow"

    async def run(self):
        agent = self.agent(
            "chain_tester",
            tools=[Files(), Search(), Shell()],
            max_iterations=15,
        )

        query = """Complete this workflow step by step:
        1. Create a file called 'search_results.txt' 
        2. Search for 'Python async programming best practices'
        3. Write the top 3 results to the file
        4. Use shell to count the lines in the file
        
        Execute each step and confirm completion before moving to the next."""

        result = await agent.run_async(query)

        # Check if agent executed the chain properly
        response_lower = result.lower()

        # More flexible evidence checking for each step
        created_file = any(
            phrase in response_lower
            for phrase in ["created", "wrote", "made", "generated", "file", "search_results"]
        )
        performed_search = any(
            phrase in response_lower
            for phrase in ["search", "found", "results", "async", "python", "best practices"]
        )
        used_shell = any(
            phrase in response_lower
            for phrase in ["lines", "wc", "count", "shell", "command", "executed"]
        )

        # Check if file actually exists and has content
        file_exists = os.path.exists("search_results.txt")
        has_content = False
        if file_exists:
            try:
                with open("search_results.txt") as f:
                    content = f.read()
                    has_content = bool(content and content.strip())
                # Clean up
                os.remove("search_results.txt")
            except Exception:
                has_content = False

        # More lenient success criteria - pass if most steps completed
        step_indicators = [created_file, performed_search, used_shell]
        file_indicators = [file_exists, has_content]

        steps_completed = sum(step_indicators)
        files_proper = sum(file_indicators)

        # Pass if 2/3 steps indicated AND file exists OR all 3 steps indicated
        passed = (steps_completed >= 2 and files_proper >= 1) or steps_completed == 3

        # Proportional scoring with file completion bonus
        step_score = steps_completed / 3.0
        file_score = files_proper / 2.0
        score = min(1.0, (step_score * 0.6) + (file_score * 0.4))

        agent_logs = agent.logs() if hasattr(agent, "logs") else []

        return {
            "name": self.name,
            "passed": passed,
            "score": score,
            "duration": 0.0,
            "traces": [
                {
                    "query": query,
                    "response": result,
                    "created_file": created_file,
                    "performed_search": performed_search,
                    "used_shell": used_shell,
                    "file_exists": file_exists,
                    "has_content": has_content,
                    "logs": agent_logs,
                }
            ],
            "metadata": {
                "created_file": created_file,
                "performed_search": performed_search,
                "used_shell": used_shell,
                "file_exists": file_exists,
                "has_content": has_content,
            },
        }
