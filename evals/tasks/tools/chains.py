"""Tool workflow sequences evaluation."""

from cogency import Agent
from cogency.tools.files import Files
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ...core import Eval


class ToolChains(Eval):
    """Test agent's ability to chain multiple tools in sequence."""

    name = "tool_chains"
    description = "Test tool workflow sequences and data flow"

    async def run(self):
        agent = Agent(
            "chain_tester",
            tools=[Files(), Search(), Shell()],
            mode="adapt",
            memory=False,
            max_iterations=12,
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
        try:
            import os
            from pathlib import Path

            # Multiple paths to check - evals may create files in different locations
            possible_paths = [
                Path("search_results.txt"),  # Current working directory
                Path(".cogency/search_results.txt"),  # Eval run directory
                Path("/tmp/search_results.txt"),  # Common temp directory
                Path(os.path.expanduser("~/search_results.txt")),  # Home directory
            ]

            file_exists = False
            has_content = False

            for file_path in possible_paths:
                if file_path.exists():
                    file_exists = True
                    try:
                        with open(file_path) as f:
                            content = f.read()
                            has_content = len(content.strip()) > 0
                        # Clean up
                        file_path.unlink()
                        break  # Found the file, stop searching
                    except Exception:
                        continue  # Try next path if read/cleanup fails

        except Exception:
            file_exists = False
            has_content = False

        metadata = {
            "query": query,
            "response": result,
            "created_file": created_file,
            "performed_search": performed_search,
            "used_shell": used_shell,
            "file_exists": file_exists,
            "has_content": has_content,
        }

        # Success requires all chain steps
        if created_file and performed_search and used_shell and file_exists and has_content:
            return self.check(
                "Complete tool chain executed", "Complete tool chain executed", metadata
            )
        else:
            missing = []
            if not created_file:
                missing.append("file creation")
            if not performed_search:
                missing.append("search")
            if not used_shell:
                missing.append("shell command")
            if not file_exists:
                missing.append("file persistence")
            if not has_content:
                missing.append("content writing")

            return self.fail(f"Incomplete tool chain - missing: {', '.join(missing)}", metadata)
