import difflib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool


@dataclass
class ReplaceParams:
    pattern: Annotated[str, ToolParam(description="Glob pattern for files to match (e.g., '*.py')")]
    old: Annotated[
        str, ToolParam(description="Text to find (exact or regex based on 'exact' flag)")
    ]
    new: Annotated[str, ToolParam(description="Replacement text")]
    exact: Annotated[
        bool, ToolParam(description="Exact string match (True) or regex pattern (False)")
    ] = True


def _prepare_glob_pattern(pattern: str, access: Access) -> str:
    if access != "sandbox":
        return pattern

    sanitized = pattern.replace("\\", "/")
    while sanitized.startswith("./"):
        sanitized = sanitized[2:]

    sanitized = sanitized.removeprefix("sandbox/")

    return sanitized or "*"


def _compute_diff(file: str, old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=file, tofile=file, lineterm="")
    return "".join(diff)


def _rollback_backups(backups: list[Path]):
    for backup_path in backups:
        if backup_path.exists():
            original_path = backup_path.with_suffix("")
            shutil.copy(backup_path, original_path)
            backup_path.unlink()


@tool("Performs find-and-replace operations across multiple files matching a glob pattern.")
@safe_execute
async def Replace(
    params: ReplaceParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs,
) -> ToolResult:
    if not params.old:
        return ToolResult(outcome="The 'old' string cannot be empty.", error=True)

    if not params.pattern:
        return ToolResult(outcome="The 'pattern' cannot be empty.", error=True)

    try:
        effective_root_for_glob = resolve_file(".", access, sandbox_dir)
    except ValueError as e:
        return ToolResult(outcome=f"Invalid access configuration: {e}", error=True)

    normalized_pattern = _prepare_glob_pattern(params.pattern, access)

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
        return ToolResult(outcome=f"No files matched the pattern '{params.pattern}'.", error=True)

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
                continue

            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy(file_path, backup_path)
            all_backups.append(backup_path)

            replacements_in_file = 0
            new_content = original_content

            if params.exact:
                occurrences = original_content.count(params.old)
                if occurrences > 1:
                    _rollback_backups(all_backups)
                    return ToolResult(
                        outcome=f"Error: Exact string '{params.old}' found multiple times in '{file_path}'. Use exact=False for regex mode or refine 'old' string.",
                        error=True,
                    )
                if occurrences == 1:
                    new_content = original_content.replace(params.old, params.new, 1)
                    replacements_in_file = 1
            else:
                try:
                    compiled_regex = re.compile(params.old)
                    new_content, replacements_in_file = compiled_regex.subn(
                        params.new, original_content
                    )
                except re.error as e:
                    _rollback_backups(all_backups)
                    return ToolResult(
                        outcome=f"Error: Invalid regex pattern '{params.old}': {e}",
                        error=True,
                    )

            if replacements_in_file > 0:
                file_path.write_text(new_content, encoding="utf-8")
                changed_files[str(file_path)] = replacements_in_file
                total_replacements += replacements_in_file
                diff = _compute_diff(str(file_path), original_content, new_content)
                all_diffs.append(diff)
            else:
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
        _rollback_backups(all_backups)
        return ToolResult(outcome=f"An unexpected error occurred: {e}", error=True)
    finally:
        for backup in all_backups:
            if backup.exists():
                backup.unlink()
