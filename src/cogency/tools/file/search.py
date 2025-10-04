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

    MAX_RESULTS = 100
    WARN_THRESHOLD = 50

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

        results = self._search_files(search_path, pattern, content)

        if not results:
            return ToolResult(outcome="Searched files", content="No matches found")

        shown = results[: self.MAX_RESULTS]
        truncated = len(results) > self.MAX_RESULTS

        content_text = "\n".join(shown)
        if truncated:
            content_text += (
                f"\n\n[Truncated: showing {self.MAX_RESULTS} of {len(results)}. Refine query.]"
            )

        return ToolResult(
            outcome=f"Found {len(results)} matches",
            content=content_text,
        )

    def _search_files(self, search_path: Path, pattern: str, content: str) -> list:
        """Search files and return clean visual results."""
        results = []

        for file_path in search_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue

            try:
                relative_path = file_path.relative_to(search_path)
            except ValueError:
                # Skip paths outside the desired root (e.g., symlinks that escape)
                continue

            if any(part.startswith(".") for part in relative_path.parts[:-1]):
                # Skip files nested under hidden directories like .git or .cogency
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
