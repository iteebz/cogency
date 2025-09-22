"""File search tool with clean visual output."""

import re
from pathlib import Path

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileSearch(Tool):
    """Search files with clean visual results."""

    name = "file_search"
    description = "Search files by pattern and content"
    schema = {
        "pattern": {"optional": True},
        "content": {"optional": True},
        "path": {"optional": True},
    }

    def __init__(self, access: Access = "sandbox"):
        self.access = access

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        query = args.get("content") or args.get("pattern", "files")
        return f'Searching files for "{query}"'

    @safe_execute
    async def execute(
        self,
        pattern: str = None,
        content: str = None,
        path: str = ".",
        **kwargs,
    ) -> ToolResult:
        """Search files with visual results."""
        if not pattern and not content:
            return ToolResult(outcome="Must specify pattern or content to search")

        # Determine search directory
        if path == ".":
            from ...lib.paths import Paths

            search_path = (
                Paths.sandbox()
                if self.access == "sandbox"
                else (Path.cwd() if self.access == "project" else Path("."))
            )
        else:
            search_path = resolve_file(path, self.access)

        if not search_path.exists():
            return ToolResult(outcome=f"Directory '{path}' does not exist")

        results = self._search_files(search_path, pattern, content)

        if not results:
            return ToolResult(outcome="No matches found")

        return ToolResult(outcome=f"Found {len(results)} matches", content="\n".join(results))

    def _search_files(self, search_path: Path, pattern: str, content: str) -> list:
        """Search files and return clean visual results."""
        results = []

        for file_path in search_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue

            # Pattern matching (filename)
            if pattern and not self._matches_pattern(file_path.name, pattern):
                continue

            file_name = file_path.name

            # Content searching
            if content:
                matches = self._search_content(file_path, content)
                for line_num, line_text in matches:
                    results.append(f"{file_name}:{line_num}: {line_text.strip()}")
            else:
                # Pattern-only search - just show filename
                results.append(file_name)

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
