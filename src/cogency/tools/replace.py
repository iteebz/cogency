import difflib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

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


def _validate_and_resolve_files(
    params: ReplaceParams, access: Access, sandbox_dir: str
) -> ToolResult | list[Path]:
    if not params.old:
        return ToolResult(outcome="The 'old' string cannot be empty.", error=True)

    if not params.pattern:
        return ToolResult(outcome="The 'pattern' cannot be empty.", error=True)

    try:
        effective_root_for_glob = resolve_file(".", access, sandbox_dir)
    except ValueError as e:
        return ToolResult(outcome=f"Invalid access configuration: {e}", error=True)

    normalized_pattern = _prepare_glob_pattern(params.pattern, access)

    matched_files: list[Path] = []
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

    return matched_files


def _format_result(matched_count: int, changed_files: dict[str, int], total: int, diffs: list[str]) -> str:
    msg = f"Matched {matched_count} files\n"
    msg += f"Changed {len(changed_files)} files\n"
    msg += f"Made {total} replacements\n\n"
    for file, count in changed_files.items():
        msg += f"{file}: {count} replacements\n"
    return msg


def _process_replacement(file_path: Path, params: ReplaceParams) -> tuple[str, int] | ToolResult:
    try:
        original_content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "", 0

    if params.exact:
        occurrences = original_content.count(params.old)
        if occurrences > 1:
            return ToolResult(
                outcome=f"Error: Exact string '{params.old}' found multiple times in '{file_path}'. Use exact=False for regex mode or refine 'old' string.",
                error=True,
            )
        if occurrences == 1:
            return original_content.replace(params.old, params.new, 1), 1
        return original_content, 0
    else:
        try:
            compiled_regex = re.compile(params.old)
            new_content, count = compiled_regex.subn(params.new, original_content)
            return new_content, count
        except re.error as e:
            return ToolResult(
                outcome=f"Error: Invalid regex pattern '{params.old}': {e}",
                error=True,
            )


@tool("Performs find-and-replace operations across multiple files matching a glob pattern.")
@safe_execute
async def Replace(
    params: ReplaceParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    files_or_error = _validate_and_resolve_files(params, access, sandbox_dir)
    if isinstance(files_or_error, ToolResult):
        return files_or_error
    matched_files = files_or_error

    changed_files: dict[str, int] = {}
    all_backups: list[Path] = []
    total_replacements = 0
    all_diffs: list[str] = []

    try:
        for file_path in matched_files:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                original_content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            shutil.copy(file_path, backup_path)
            all_backups.append(backup_path)

            result = _process_replacement(file_path, params)
            if isinstance(result, ToolResult):
                _rollback_backups(all_backups)
                return result

            new_content, replacements_in_file = result

            if replacements_in_file > 0:
                file_path.write_text(new_content, encoding="utf-8")
                changed_files[str(file_path)] = replacements_in_file
                total_replacements += replacements_in_file
                diff = _compute_diff(str(file_path), original_content, new_content)
                all_diffs.append(diff)
            else:
                backup_path.unlink()
                all_backups.remove(backup_path)

        outcome_msg = _format_result(
            len(matched_files), changed_files, total_replacements, all_diffs
        )
        return ToolResult(outcome=outcome_msg, content="\n".join(all_diffs))

    except Exception as e:
        _rollback_backups(all_backups)
        return ToolResult(outcome=f"An unexpected error occurred: {e}", error=True)
    finally:
        for backup in all_backups:
            if backup.exists():
                backup.unlink()
