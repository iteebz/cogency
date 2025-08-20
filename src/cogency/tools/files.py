"""Files: File operations for sandbox environment."""

from pathlib import Path

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result
from .security import safe_path, validate_input


class FileRead(Tool):
    """Enhanced file reading with intelligent context and formatting."""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read file content with intelligent formatting. Args: filename (str)"

    @property
    def schema(self) -> dict:
        return {
            "filename": {"type": "str", "required": True, "description": "Path to file to read"}
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "Read config file", "call": {"filename": "config.json"}},
            {"task": "Read source code", "call": {"filename": "main.py"}},
            {"task": "Read documentation", "call": {"filename": "README.md"}},
        ]

    async def execute(self, filename: str) -> Result[str, str]:
        if not filename:
            return Err("Filename cannot be empty")

        try:
            sandbox_dir = Path(".sandbox")
            file_path = safe_path(sandbox_dir, filename)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Enhanced formatting with context
            formatted = self._format_content(filename, content, file_path)
            return Ok(formatted)

        except FileNotFoundError:
            return Err(f"File not found: {filename}\n💡 Use 'list' to see available files")
        except UnicodeDecodeError:
            return Err(f"File '{filename}' contains binary data - cannot display as text")
        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to read '{filename}': {str(e)}")

    def _format_content(self, filename: str, content: str, file_path: Path) -> str:
        """Format file content with intelligent context."""
        if not content:
            return f"📄 {filename} (empty file)"

        # Get file stats
        stat = file_path.stat()
        size = self._format_size(stat.st_size)
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = self._categorize_file(file_path)

        # Build header with context
        header = f"📄 {filename} ({size}, {line_count} lines) [{category}]"

        # Add syntax context for code files
        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        # Handle large files intelligently
        if len(content) > 5000:
            preview = content[:5000]
            return f"{header}\n\n{preview}\n\n[File truncated at 5,000 characters. Full size: {len(content):,} chars]\n💡 File is large - consider using 'shell' with 'head' or 'tail' for specific sections"

        return f"{header}\n\n{content}"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size human-readable."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        return f"{size_bytes / (1024 * 1024):.1f}MB"

    def _categorize_file(self, file_path: Path) -> str:
        """Smart file categorization for context."""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()

        # Configuration files
        if any(x in name for x in ["config", "settings", ".env", ".ini"]) or ext in [
            ".toml",
            ".yaml",
            ".yml",
            ".json",
            ".ini",
        ]:
            return "config"

        # Source code
        if ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"]:
            return "code"

        # Documentation
        if ext in [".md", ".rst", ".txt", ".doc", ".docx"] or name in [
            "readme",
            "license",
            "changelog",
        ]:
            return "docs"

        # Data files
        if ext in [".csv", ".json", ".xml", ".sql", ".db", ".sqlite"]:
            return "data"

        # Tests
        if "test" in name or name.startswith("spec_"):
            return "test"

        return "text"


class FileWrite(Tool):
    """Enhanced file writing with intelligent feedback and context awareness."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return (
            "Write content to file with intelligent feedback. Args: filename (str), content (str)"
        )

    @property
    def schema(self) -> dict:
        return {
            "filename": {"type": "str", "required": True, "description": "Path to file to write"},
            "content": {"type": "str", "required": True, "description": "Content to write to file"},
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {
                "task": "Create Python script",
                "call": {"filename": "hello.py", "content": "print('Hello, world!')"},
            },
            {
                "task": "Save configuration",
                "call": {"filename": "config.json", "content": '{"debug": true}'},
            },
            {
                "task": "Write documentation",
                "call": {
                    "filename": "README.md",
                    "content": "# Project Title\n\nDescription here.",
                },
            },
        ]

    async def execute(self, filename: str, content: str) -> Result[str, str]:
        if not filename:
            return Err("Filename cannot be empty")

        if not validate_input(content):
            return Err("Content contains unsafe patterns")

        try:
            # Ensure sandbox directory exists
            sandbox_dir = Path(".sandbox")
            sandbox_dir.mkdir(exist_ok=True)

            file_path = safe_path(sandbox_dir, filename)

            # Check if overwriting existing file
            is_overwrite = file_path.exists()
            old_size = file_path.stat().st_size if is_overwrite else 0

            # Write with UTF-8 encoding
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Enhanced feedback with context
            result = self._format_write_result(filename, content, file_path, is_overwrite, old_size)
            return Ok(result)

        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to write '{filename}': {str(e)}")

    def _format_write_result(
        self, filename: str, content: str, file_path: Path, is_overwrite: bool, old_size: int
    ) -> str:
        """Format write result with intelligent context."""
        # Basic metrics
        size = self._format_size(len(content.encode("utf-8")))
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = self._categorize_file(file_path)

        # Build result message
        action = "Updated" if is_overwrite else "Created"
        header = f"✓ {action} '{filename}' ({size}, {line_count} lines) [{category}]"

        # Add syntax context for code files
        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        # Add change context for overwrites
        if is_overwrite:
            old_size_formatted = self._format_size(old_size)
            if old_size != len(content.encode("utf-8")):
                change = "larger" if len(content.encode("utf-8")) > old_size else "smaller"
                header += f"\nSize change: {old_size_formatted} → {size} ({change})"

        # Add helpful context
        context = self._get_write_context(filename, content, category)
        if context:
            header += f"\n💡 {context}"

        return header

    def _get_write_context(self, filename: str, content: str, category: str) -> str:
        """Provide intelligent context for written files."""
        # Python files
        if category == "code" and filename.endswith(".py"):
            if "def " in content or "class " in content:
                return "Python code detected. Use 'shell python filename.py' to execute."
            return "Python script ready. Use 'shell python filename.py' to run."

        # JavaScript/Node files
        if category == "code" and filename.endswith((".js", ".ts")):
            if "function " in content or "const " in content:
                return "JavaScript code detected. Use 'shell node filename.js' to execute."

        # Configuration files
        elif category == "config":
            return "Configuration file saved. Changes may require restart of related services."

        # Data files
        elif category == "data":
            if filename.endswith(".csv"):
                return "CSV data saved. Use 'read filename.csv' to verify or 'shell head filename.csv' for preview."
            if filename.endswith(".json"):
                return "JSON data saved. Use 'read filename.json' to verify structure."

        # Large files
        elif len(content) > 10000:
            return "Large file created. Use 'shell head filename' or 'shell tail filename' for previews."

        # Documentation
        elif category == "docs":
            return "Documentation saved. Use 'read filename' to review content."

        return None

    def _format_size(self, size_bytes: int) -> str:
        """Format file size human-readable."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        return f"{size_bytes / (1024 * 1024):.1f}MB"

    def _categorize_file(self, file_path: Path) -> str:
        """Smart file categorization for context."""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()

        # Configuration files
        if any(x in name for x in ["config", "settings", ".env", ".ini"]) or ext in [
            ".toml",
            ".yaml",
            ".yml",
            ".json",
            ".ini",
        ]:
            return "config"

        # Source code
        if ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"]:
            return "code"

        # Documentation
        if ext in [".md", ".rst", ".txt", ".doc", ".docx"] or name in [
            "readme",
            "license",
            "changelog",
        ]:
            return "docs"

        # Data files
        if ext in [".csv", ".json", ".xml", ".sql", ".db", ".sqlite"]:
            return "data"

        # Tests
        if "test" in name or name.startswith("spec_"):
            return "test"

        return "text"


class FileList(Tool):
    """Enhanced file listing with hierarchical context and intelligence."""

    @property
    def name(self) -> str:
        return "list"

    @property
    def description(self) -> str:
        return "List files with hierarchical structure and intelligence. Args: depth (int, default 2), pattern (str, default '*'), details (bool, default False), show_hidden (bool, default False)"

    @property
    def schema(self) -> dict:
        return {
            "depth": {
                "type": "int",
                "required": False,
                "default": 2,
                "description": "Directory depth to traverse",
            },
            "pattern": {
                "type": "str",
                "required": False,
                "default": "*",
                "description": "File pattern to match (e.g., '*.py', '*test*')",
            },
            "details": {
                "type": "bool",
                "required": False,
                "default": False,
                "description": "Show detailed file information",
            },
            "show_hidden": {
                "type": "bool",
                "required": False,
                "default": False,
                "description": "Include hidden files and directories",
            },
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "List all files", "call": {}},
            {"task": "List Python files only", "call": {"pattern": "*.py"}},
            {"task": "Show detailed file info", "call": {"details": True}},
            {"task": "Deep directory scan", "call": {"depth": 4}},
            {"task": "Find test files", "call": {"pattern": "*test*", "depth": 3}},
        ]

    async def execute(
        self,
        depth: int = 2,
        pattern: str = "*",
        details: bool = False,
        show_hidden: bool = False,
    ) -> Result[str, str]:
        """Enhanced file listing with LS-style context intelligence."""
        try:
            sandbox = Path(".sandbox")
            if not sandbox.exists():
                return Ok("Sandbox directory is empty")

            # Build hierarchical structure
            tree = self._build_tree(sandbox, depth, pattern, show_hidden)
            if not tree:
                return Ok("No files match the specified pattern")

            # Format with beautiful tree structure
            result = self._format_tree(tree, details, sandbox)
            summary = self._get_summary(tree)

            return Ok(f"{result}\n\n{summary}")

        except Exception as e:
            return Err(f"Error listing files: {str(e)}")

    def _build_tree(
        self, path: Path, max_depth: int, pattern: str, show_hidden: bool, current_depth: int = 0
    ) -> dict:
        """Build hierarchical file structure like LS tool."""
        tree = {"dirs": {}, "files": []}

        if current_depth >= max_depth:
            return tree

        try:
            for item in sorted(path.iterdir()):
                # Skip hidden files unless requested
                if not show_hidden and item.name.startswith("."):
                    continue

                if item.is_dir():
                    subtree = self._build_tree(
                        item, max_depth, pattern, show_hidden, current_depth + 1
                    )
                    if subtree["dirs"] or subtree["files"]:  # Only include non-empty dirs
                        tree["dirs"][item.name] = subtree

                elif item.is_file():
                    # Apply pattern matching
                    if self._matches_pattern(item.name, pattern):
                        stat = item.stat()
                        tree["files"].append(
                            {
                                "name": item.name,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "category": self._categorize_file(item),
                            }
                        )

        except PermissionError:
            pass  # Skip inaccessible directories

        return tree

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcards)."""
        if pattern == "*":
            return True

        # Convert shell-style wildcards to simple matching
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return filename.startswith(prefix) and filename.endswith(suffix)

        return pattern.lower() in filename.lower()

    def _categorize_file(self, file_path: Path) -> str:
        """Smart file categorization for context."""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()

        # Configuration files
        if any(x in name for x in ["config", "settings", ".env", ".ini"]) or ext in [
            ".toml",
            ".yaml",
            ".yml",
            ".json",
            ".ini",
        ]:
            return "config"

        # Source code
        if ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"]:
            return "code"

        # Documentation
        if ext in [".md", ".rst", ".txt", ".doc", ".docx"] or name in [
            "readme",
            "license",
            "changelog",
        ]:
            return "docs"

        # Data files
        if ext in [".csv", ".json", ".xml", ".sql", ".db", ".sqlite"]:
            return "data"

        # Tests
        if "test" in name or name.startswith("spec_"):
            return "test"

        # Build/Package
        if name in ["package.json", "requirements.txt", "cargo.toml", "pom.xml", "build.gradle"]:
            return "build"

        return "misc"

    def _format_tree(self, tree: dict, details: bool, base_path: Path) -> str:
        """Format as beautiful tree structure."""
        lines = [f"Sandbox Structure ({base_path.name}):"]
        self._format_tree_recursive(tree, lines, "", details)
        return "\n".join(lines)

    def _format_tree_recursive(self, tree: dict, lines: list, prefix: str, details: bool):
        """Recursively format tree structure."""
        items = []

        # Add directories first
        for dir_name, subtree in tree["dirs"].items():
            items.append(("dir", dir_name, subtree))

        # Add files second
        for file_info in tree["files"]:
            items.append(("file", file_info, None))

        for i, (item_type, item_data, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if item_type == "dir":
                lines.append(f"{prefix}{current_prefix}{item_data}/")
                self._format_tree_recursive(subtree, lines, next_prefix, details)
            else:
                # File formatting
                file_info = item_data
                name = file_info["name"]
                size = self._format_size(file_info["size"])
                category = file_info["category"]

                if details:
                    import time

                    mod_time = time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(file_info["modified"])
                    )
                    lines.append(
                        f"{prefix}{current_prefix}{name:<20} {size:>8} {mod_time} [{category}]"
                    )
                else:
                    lines.append(f"{prefix}{current_prefix}{name} ({size}) [{category}]")

    def _format_size(self, size_bytes: int) -> str:
        """Format file size human-readable."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        return f"{size_bytes / (1024 * 1024):.1f}MB"

    def _get_summary(self, tree: dict) -> str:
        """Generate project summary for agent context."""
        total_files = 0
        total_dirs = 0
        total_size = 0
        categories = {}

        def count_recursive(subtree):
            nonlocal total_files, total_dirs, total_size

            total_dirs += len(subtree["dirs"])
            total_files += len(subtree["files"])

            for file_info in subtree["files"]:
                total_size += file_info["size"]
                category = file_info["category"]
                categories[category] = categories.get(category, 0) + 1

            for subdir_tree in subtree["dirs"].values():
                count_recursive(subdir_tree)

        count_recursive(tree)

        summary_parts = [
            f"Total: {total_files} files, {total_dirs} directories, {self._format_size(total_size)}"
        ]

        if categories:
            cat_summary = ", ".join([f"{count} {cat}" for cat, count in sorted(categories.items())])
            summary_parts.append(f"Types: {cat_summary}")

        return " | ".join(summary_parts)
