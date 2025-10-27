import difflib
import re
import shutil
from pathlib import Path

from ..core.config import Access
from ..core.protocols import Tool, ToolResult
from ..core.security import resolve_file, safe_execute


class Replace(Tool):
    """Performs find-and-replace operations across multiple files."""

    name = "replace"
    description = (
        "Performs find-and-replace operations across multiple files matching a glob pattern."
    )
    schema = {
        "pattern": {"type": "string"},
        "old": {"type": "string"},
        "new": {"type": "string"},
        "exact": {"type": "boolean", "optional": True, "default": True},
    }

    def describe(self, args: dict) -> str:
        pattern = args.get("pattern", "files")
        old = args.get("old", "text")
        new = args.get("new", "replacement")
        exact = args.get("exact", True)
        mode = "exact" if exact else "regex"
        return f"Replacing '{old}' with '{new}' ({mode} mode) in files matching '{pattern}'"

    @safe_execute
    async def execute(
        self,
        pattern: str,
        old: str,
        new: str,
        exact: bool = True,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not old:
            return ToolResult(outcome="The 'old' string cannot be empty.", error=True)

        if not pattern:
            return ToolResult(outcome="The 'pattern' cannot be empty.", error=True)

        try:
            effective_root_for_glob = resolve_file(".", access, sandbox_dir)
        except ValueError as e:
            return ToolResult(outcome=f"Invalid access configuration: {e}", error=True)

        normalized_pattern = self._prepare_glob_pattern(pattern, access)

        matched_files = []
        for p in effective_root_for_glob.glob(normalized_pattern):
            if p.is_file():
                try:
                    resolved_path = resolve_file(
                        str(p.relative_to(effective_root_for_glob)), access, sandbox_dir
                    )
                    matched_files.append(resolved_path)
                except ValueError:
                    continue

        if not matched_files:
            return ToolResult(outcome=f"No files matched the pattern '{pattern}'.", error=True)

        if len(matched_files) > 1000:
            return ToolResult(
                outcome=f"Too many files ({len(matched_files)}) matched the pattern. Limit is 1000 to prevent accidental mass destruction.",
                error=True,
            )

        changed_files = {}
        all_backups = []
        total_replacements = 0
        all_diffs = []

        try:
            for file_path in matched_files:
                try:
                    original_content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Skip binary files
                    continue

                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy(file_path, backup_path)
                all_backups.append(backup_path)

                replacements_in_file = 0
                new_content = original_content

                if exact:
                    occurrences = original_content.count(old)
                    if occurrences > 1:
                        self._rollback_backups(all_backups)
                        return ToolResult(
                            outcome=f"Error: Exact string '{old}' found multiple times in '{file_path}'. Use exact=False for regex mode or refine 'old' string.",
                            error=True,
                        )
                    if occurrences == 1:
                        new_content = original_content.replace(old, new, 1)
                        replacements_in_file = 1
                else:  # Regex mode
                    try:
                        compiled_regex = re.compile(old)
                        new_content, replacements_in_file = compiled_regex.subn(
                            new, original_content
                        )
                    except re.error as e:
                        self._rollback_backups(all_backups)
                        return ToolResult(
                            outcome=f"Error: Invalid regex pattern '{old}': {e}",
                            error=True,
                        )

                if replacements_in_file > 0:
                    file_path.write_text(new_content, encoding="utf-8")
                    changed_files[str(file_path)] = replacements_in_file
                    total_replacements += replacements_in_file
                    diff = self._compute_diff(str(file_path), original_content, new_content)
                    all_diffs.append(diff)
                else:
                    # If no replacements, remove the backup
                    backup_path.unlink()
                    all_backups.remove(backup_path)

            outcome_message = f"Matched {len(matched_files)} files\n"
            outcome_message += f"Changed {len(changed_files)} files\n"
            outcome_message += f"Made {total_replacements} replacements\n\n"

            for file, count in changed_files.items():
                outcome_message += f"{file}: {count} replacements\n"

            final_diff_content = "\n".join(all_diffs)

            return ToolResult(outcome=outcome_message, content=final_diff_content)

        except Exception as e:
            self._rollback_backups(all_backups)
            return ToolResult(outcome=f"An unexpected error occurred: {e}", error=True)
        finally:
            # Clean up backups for successfully processed files
            for backup in all_backups:
                if backup.exists():
                    backup.unlink()

    def _prepare_glob_pattern(self, pattern: str, access: Access) -> str:
        """Normalize sandbox-prefixed patterns so they align with other tools."""
        if access != "sandbox":
            return pattern

        sanitized = pattern.replace("\\", "/")
        while sanitized.startswith("./"):
            sanitized = sanitized[2:]

        if sanitized.startswith("sandbox/"):
            sanitized = sanitized[len("sandbox/") :]

        return sanitized or "*"

    def _compute_diff(self, file: str, old: str, new: str) -> str:
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, fromfile=file, tofile=file, lineterm="")
        return "".join(diff)

    def _rollback_backups(self, backups: list[Path]):
        """Restores files from backups and cleans up backup files."""
        for backup_path in backups:
            if backup_path.exists():
                original_path = backup_path.with_suffix("")
                shutil.copy(backup_path, original_path)
                backup_path.unlink()
