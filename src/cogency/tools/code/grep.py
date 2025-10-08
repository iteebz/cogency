import re
from pathlib import Path

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class Grep(Tool):
    """Search files."""

    name = "grep"
    description = "Search files."
    schema = {
        "pattern": {"optional": True},
        "content": {"optional": True},
        "path": {"optional": True},
    }

    MAX_RESULTS = 100
    WARN_THRESHOLD = 50

    def describe(self, args: dict) -> str:
        query = args.get("content") or args.get("pattern", "files")
        return f'Searching files for "{query}"'

    @safe_execute
    async def execute(
        self,
        pattern: str = None,
        content: str = None,
        path: str = ".",
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not pattern and not content:
            return ToolResult(outcome="Must specify pattern or content to search", error=True)

        if pattern == "*" and not content:
            return ToolResult(
                outcome="Pattern too broad",
                content="Specify: content='...' OR pattern='*.py' OR path='subdir'",
                error=True,
            )

        if path == ".":
            if access == "sandbox":
                search_path = Path(sandbox_dir).resolve()
                search_path.mkdir(parents=True, exist_ok=True)
            else:
                search_path = Path.cwd().resolve()
        else:
            search_path = resolve_file(path, access, sandbox_dir).resolve()

        workspace_root = search_path if access == "sandbox" else Path.cwd().resolve()

        # Ensure search never escapes the workspace root, even if the resolved
        # path is a symlink. is_relative_to is available on Python 3.9+.
        if not search_path.is_relative_to(workspace_root):
            return ToolResult(
                outcome="Directory outside workspace scope",
                error=True,
            )

        if not search_path.exists():
            return ToolResult(outcome=f"Directory '{path}' does not exist", error=True)

        results = self._search_files(search_path, workspace_root, pattern, content)
        total = len(results)

        def describe_root() -> str:
            try:
                relative = search_path.relative_to(workspace_root)
                return "." if str(relative) == "." else str(relative)
            except ValueError:
                return "."

        def describe_query() -> list[str]:
            lines = [f"Search root: {describe_root()}"]
            if pattern:
                lines.append(f"Pattern: {pattern}")
            if content:
                lines.append(f"Content: {content}")
            return lines

        if total == 0:
            summary = "\n".join(describe_query())
            return ToolResult(
                outcome="Found 0 matches",
                content=summary,
            )

        lines = describe_query()
        lines.append("")

        shown = results[: self.MAX_RESULTS]
        truncated = total > self.MAX_RESULTS

        content_text = "\n".join(lines + shown)
        if truncated:
            content_text += f"\n\n[Truncated: showing {self.MAX_RESULTS} of {total}. Refine query.]"

        return ToolResult(
            outcome=f"Found {total} {'match' if total == 1 else 'matches'}",
            content=content_text,
        )

    SKIP_DIRS = {
        ".venv",
        "venv",
        ".env",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".git",
        ".hatch",
        ".tox",
        ".nox",
        "dist",
        "build",
        ".eggs",
    }

    def _search_files(
        self,
        search_path: Path,
        workspace_root: Path,
        pattern: str,
        content: str,
    ) -> list:
        """Search files and return clean visual results."""
        results = []
        root = workspace_root

        def walk(p: Path):
            try:
                for item in p.iterdir():
                    if (
                        item.name.startswith(".")
                        or item.name in self.SKIP_DIRS
                        or item.name.endswith(".egg-info")
                    ):
                        continue

                    if item.is_dir():
                        walk(item)
                    elif item.is_file():
                        if pattern and not self._matches_pattern(item.name, pattern):
                            continue
                        try:
                            relative_path = item.relative_to(root)
                        except ValueError:
                            continue
                        path_str = str(relative_path)

                        if content:
                            matches = self._search_content(item, content)
                            for line_num, line_text in matches:
                                results.append(f"{path_str}:{line_num}: {line_text.strip()}")
                        else:
                            results.append(path_str)
            except PermissionError:
                pass

        walk(search_path)
        return results

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Pattern matching with wildcards."""
        if pattern == "*":
            return True

        if "*" in pattern:
            # Convert shell wildcards to regex
            regex_pattern = pattern.replace("*", ".*")
            return bool(re.match(regex_pattern, filename, re.IGNORECASE))

        return pattern.lower() in filename.lower()

    def _search_content(self, file_path: Path, search_term: str) -> list:
        """Search file content and return (line_num, line_text) tuples."""
        matches = []

        try:
            with open(file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if search_term.lower() in line.lower():
                        matches.append((line_num, line))
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or inaccessible files
            pass

        return matches
