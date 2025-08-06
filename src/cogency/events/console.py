"""Console output for development."""


class ConsoleHandler:
    """Clean CLI output using canonical symbol system."""

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = debug
        self._needs_user_newline = True  # Track if we need newline after user input
        self._recent_thinking = []  # Track recent thinking to avoid repetition

    def handle(self, event):
        if not self.enabled:
            return

        event_type = event["type"]
        data = {**event.get("data", {}), **event}

        # User input - show with > symbol per cli.md spec
        if event_type == "start":
            self._needs_user_newline = True  # Reset flag for new interaction
            query = data.get("query", "")
            if query:
                print(f"> {query.strip()}")
            return

        # Thinking states - show with proper symbols
        elif event_type == "reason":
            content = data.get("content", "").strip()

            if content and not content.startswith("✻ Thinking"):
                self._needs_user_newline = False

                # Skip repetitive or overly verbose thinking
                if self._is_repetitive_thinking(content):
                    return

                # Detect deep vs quick thinking
                # * for deep thinking: analysis, planning, complex reasoning
                # ◦ for quick thinking: simple decisions, next steps
                is_deep = (
                    any(
                        keyword in content.lower()
                        for keyword in [
                            "analyze",
                            "consider",
                            "strategy",
                            "approach",
                            "architecture",
                            "pattern",
                            "design",
                            "structure",
                            "planning",
                            "reviewing",
                            "examining",
                            "evaluating",
                            "determining",
                            "understanding",
                        ]
                    )
                    or len(content) > 150
                )

                symbol = "*" if is_deep else "◦"
                print(f"{symbol} {content}")

        # Tool actions
        elif event_type == "action" and data.get("state") == "executing":
            self._needs_user_newline = False

            tool = data.get("tool", "")
            input_text = data.get("input", "")

            if tool == "shell":
                cmd = self._extract_shell_command(input_text)
                display = f"Shell({cmd})" if cmd else "Shell()"
                print(f"• {display}")

            elif tool == "files":
                operation = self._extract_file_operation(input_text)
                if self.debug:  # Only show debug when debug is enabled
                    print(f"DEBUG: input_text = {repr(input_text)}, operation = {operation}")
                print(f"• {operation}")

            elif tool == "scrape":
                url = self._extract_scrape_url(input_text)
                display = f"Scrape({url})" if url else "Scrape()"
                print(f"• {display}")

            elif tool == "search":
                query = self._extract_search_query(input_text)
                display = f"Search({query})" if query else "Search()"
                print(f"• {display}")

            else:
                # For unknown tools, try to extract any meaningful input
                generic_input = self._extract_generic_input(input_text)
                display = (
                    f"{tool.title()}({generic_input})" if generic_input else f"{tool.title()}()"
                )
                print(f"• {display}")

        # Tool results - only show final success, skip failures
        elif event_type == "tool":
            name = data.get("name", "tool")
            result = data.get("result", "")
            success = data.get("ok", False)

            # Only show successful tool results
            if success:
                summary = self._format_success_result(name, result)
                print(f"✓ {summary}")

        # Error events
        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"✗ {message}")

        # Debug events (only when debug enabled)
        elif event_type == "debug" and self.debug:
            message = data.get("message", "Debug info")
            print(f"[DEBUG] {message}")

        # Agent completion
        elif event_type == "agent_complete":
            response = data.get("response", "Task completed")
            # Clean up markdown formatting for CLI display
            clean_response = self._clean_markdown(response)
            print(f"→ {clean_response}")

    def _extract_shell_command(self, input_text):
        """Extract command from shell tool input."""
        try:
            # Handle string format
            if isinstance(input_text, str):
                import re

                # Try parentheses format first (from format_human) like "(ls -la)"
                paren_match = re.search(r"\(([^)]+)\)", input_text)
                if paren_match:
                    return paren_match.group(1).strip()

                # Try JSON format for backward compatibility
                # Try to extract from nested args structure
                args_match = re.search(r'"args":\s*{([^}]+)}', input_text)
                if args_match:
                    args_content = args_match.group(1)
                    cmd_match = re.search(r'"command":\s*"([^"]+)"', args_content)
                    if cmd_match:
                        return cmd_match.group(1)

                # Try direct JSON format
                if "command" in input_text:
                    match = re.search(r'"command":\s*"([^"]+)"', input_text)
                    if match:
                        return match.group(1)

                # If it looks like a direct command, use it
                if input_text.strip() and not input_text.startswith("{"):
                    return input_text.strip()

            # Handle dict format
            elif isinstance(input_text, dict):
                # Check if it's the full tool call format
                if "args" in input_text:
                    args = input_text["args"]
                    cmd = args.get("command", "")
                else:
                    cmd = input_text.get("command", "")
                return cmd if cmd else ""
        except Exception:
            pass
        return ""

    def _extract_file_operation(self, input_text):
        """Extract file operation details."""
        try:
            # Handle human-readable format from format_human() like "(create, demo.py)"
            if isinstance(input_text, str):
                import re

                # Try parentheses format first (from format_human)
                paren_match = re.search(r"\(([^)]+)\)", input_text)
                if paren_match:
                    content = paren_match.group(1).strip()
                    parts = [p.strip() for p in content.split(",")]

                    if len(parts) >= 2:
                        action = parts[0].lower()
                        path = parts[1]

                        if action == "create":
                            return f"Create({path})"
                        elif action == "read":
                            return f"Read({path})"
                        elif action == "edit":
                            return f"Update({path})"
                        elif action == "list":
                            return f"List({path})" if path else "List(.)"
                        else:
                            return f"{action.title()}({path})"
                    elif len(parts) == 1:
                        # Single argument - Files tool uses path as primary arg
                        path = parts[0]
                        # Since we can't determine action from format_human output,
                        # use generic Files(path) format
                        return f"Files({path})"

                # Try JSON format for backward compatibility
                if "action" in input_text:
                    # Try to extract from nested args structure
                    args_match = re.search(r'"args":\s*{([^}]+)}', input_text)
                    if args_match:
                        args_content = args_match.group(1)
                        action_match = re.search(r'"action":\s*"([^"]+)"', args_content)
                        path_match = re.search(r'"path":\s*"([^"]+)"', args_content)
                    else:
                        # Try direct format
                        action_match = re.search(r'"action":\s*"([^"]+)"', input_text)
                        path_match = re.search(r'"path":\s*"([^"]+)"', input_text)

                    action = action_match.group(1) if action_match else ""
                    path = path_match.group(1) if path_match else ""

                    if action == "create" and path:
                        return f"Create({path})"
                    elif action == "read" and path:
                        return f"Read({path})"
                    elif action == "edit" and path:
                        return f"Update({path})"
                    elif action == "list":
                        return f"List({path})" if path else "List(.)"
                    elif action and path:
                        return f"{action.title()}({path})"

            # Handle dict format
            elif isinstance(input_text, dict):
                # Check if it's the full tool call format
                if "args" in input_text:
                    args = input_text["args"]
                    action = args.get("action", "")
                    path = args.get("path", "")
                else:
                    action = input_text.get("action", "")
                    path = input_text.get("path", "")

                if action == "create" and path:
                    return f"Create({path})"
                elif action == "read" and path:
                    return f"Read({path})"
                elif action == "edit" and path:
                    return f"Update({path})"
                elif action == "list":
                    return f"List({path})" if path else "List(.)"
                elif action and path:
                    return f"{action.title()}({path})"
        except Exception:
            pass
        return "Files()"

    def _extract_scrape_url(self, input_text):
        """Extract URL from scrape tool input."""
        try:
            if isinstance(input_text, dict):
                return input_text.get("url", "")
            elif isinstance(input_text, str):
                # Handle format like "(https://example.com)"
                import re

                url_match = re.search(r"\((https?://[^)]+)\)", input_text)
                if url_match:
                    return url_match.group(1)
                # Handle JSON format
                elif "url" in input_text:
                    match = re.search(r'"url":\s*"([^"]+)"', input_text)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return ""

    def _extract_search_query(self, input_text):
        """Extract query from search tool input."""
        try:
            if isinstance(input_text, dict):
                return input_text.get("query", "")
            elif isinstance(input_text, str):
                # Handle parentheses format like (search query)
                import re

                match = re.search(r"\(([^)]+)\)", input_text)
                if match:
                    return match.group(1).strip()
                # Handle JSON format
                elif "query" in input_text:
                    match = re.search(r'"query":\s*"([^"]+)"', input_text)
                    if match:
                        return match.group(1)
                # Handle direct string if it looks like a query
                elif len(input_text.strip()) > 0 and not input_text.startswith("{"):
                    return input_text.strip()
        except Exception:
            pass
        return ""

    def _extract_generic_input(self, input_text):
        """Extract any meaningful input from unknown tool formats."""
        try:
            if isinstance(input_text, dict):
                # Look for common parameter names
                for key in ["query", "text", "content", "data", "input", "value"]:
                    if key in input_text and input_text[key]:
                        return str(input_text[key])
            elif isinstance(input_text, str) and input_text.strip():
                # Try to extract from JSON-like format
                import re

                # Look for any quoted value
                matches = re.findall(r'"[^"]*":\s*"([^"]+)"', input_text)
                if matches:
                    return matches[0]
        except Exception:
            pass
        return ""

    def _format_success_result(self, tool_name, result):
        """Format successful tool results with meaningful summaries."""
        if tool_name == "shell":
            lines = result.split("\n") if result else []
            output_lines = [
                line.strip() for line in lines if line.strip() and not line.startswith("command:")
            ]

            if not output_lines:
                return "Command completed"

            # Show package installs, test results, etc.
            first_line = output_lines[0]
            if "successfully installed" in first_line.lower():
                packages = first_line.split("Successfully installed")[1].strip()
                package_count = packages.count(" ") + 1
                return f"{package_count} packages installed"
            elif "failed" in first_line.lower() and "passed" in first_line.lower():
                return first_line
            elif "exit code:" in first_line.lower():
                return "Command completed"
            elif len(output_lines) == 1:
                return first_line[:50] + "..." if len(first_line) > 50 else first_line
            else:
                return f"Command completed ({len(output_lines)} lines)"

        elif tool_name == "files":
            if "Created file:" in result or "File created" in result:
                # Extract filename from result
                import re

                filename_match = re.search(r"(?:Created file:|File created)\s*([^\n]+)", result)
                if filename_match:
                    filename = filename_match.group(1).strip()
                    return f"File created ({filename})"
                return "File created"
            elif "Read file:" in result:
                lines = result.count("\n")
                return f"File read ({lines} lines)" if lines > 0 else "File read"
            elif "Edited" in result or "Replaced" in result:
                return "File updated"
            else:
                return (
                    result.split("\n")[0][:50] + "..."
                    if result and len(result.split("\n")[0]) > 50
                    else result.split("\n")[0]
                    if result
                    else "Operation completed"
                )

        elif tool_name == "search":
            if "Found" in result and "results" in result:
                import re

                match = re.search(r"Found (\d+) results", result)
                if match:
                    count = match.group(1)
                    return f"{count} search results found"
            return "Search completed"

        elif tool_name == "scrape":
            if "content" in result.lower():
                return "Content scraped successfully"
            return "Scrape completed"

        return (
            result[:50] + "..."
            if result and len(result) > 50
            else result
            if result
            else "Completed"
        )

    def _clean_markdown(self, text):
        """Clean markdown formatting for CLI display."""
        import re

        # Remove markdown headers
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        # Remove markdown bold/italic
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)

        # Convert markdown links to plain text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Convert bullet points
        text = re.sub(r"^\*\s+", "• ", text, flags=re.MULTILINE)
        text = re.sub(r"^\-\s+", "• ", text, flags=re.MULTILINE)

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text.strip()

    def _is_repetitive_thinking(self, content):
        """Check if thinking content is repetitive or redundant."""
        # Keep only last 3 thinking entries for comparison
        if len(self._recent_thinking) > 3:
            self._recent_thinking = self._recent_thinking[-3:]

        # Check for exact duplicates
        if content in self._recent_thinking:
            return True

        # Check for very similar content (>80% overlap)
        for recent in self._recent_thinking:
            if self._similarity_ratio(content, recent) > 0.8:
                return True

        # Add to recent thinking
        self._recent_thinking.append(content)
        return False

    def _similarity_ratio(self, text1, text2):
        """Calculate similarity ratio between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)
