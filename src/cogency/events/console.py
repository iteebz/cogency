"""Console output for development."""

import re

from .thinking import format_thinking, is_repetitive_thinking
from .tool_formatter import format_tool_action


class ConsoleHandler:
    """Clean CLI output using canonical symbol system."""

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = debug
        self._needs_user_newline = True
        self._recent_thinking = []

    def handle(self, event):
        if not self.enabled:
            return

        event_type = event["type"]
        data = {**event.get("data", {}), **event}

        # User input - show with > symbol per cli.md spec
        if event_type == "start":
            self._needs_user_newline = True
            query = data.get("query", "")
            if query:
                print(f"> {query.strip()}")
            return

        # Thinking states - show with proper symbols
        if event_type == "reason":
            content = data.get("content", "").strip()

            if content and not content.startswith("✻ Thinking"):
                self._needs_user_newline = False

                if is_repetitive_thinking(content, self._recent_thinking):
                    return

                print(format_thinking(content))
                self._recent_thinking.append(content)
                if len(self._recent_thinking) > 5:
                    self._recent_thinking.pop(0)

        # Tool actions
        elif event_type == "action" and data.get("state") == "executing":
            self._needs_user_newline = False

            tool = data.get("tool", "")
            input_text = data.get("input", "")
            display = format_tool_action(tool, input_text)

            if self.debug and tool == "files":
                print(f"DEBUG: input_text = {repr(input_text)}")

            print(f"• {display}")

        # Tool results
        elif event_type == "action" and data.get("state") == "success":
            # Extract meaningful result summary
            result = data.get("result", "")
            tool_name = data.get("tool", "")

            summary = self._format_result_summary(tool_name, result)
            if summary:
                print(f"  {summary}")

        # Agent completion
        elif event_type == "agent" and data.get("state") == "complete":
            # Ensure clean output spacing
            if not self._needs_user_newline:
                print()  # Add newline separation

            response = data.get("response", "Task completed")
            clean_response = self._clean_markdown(response)
            print(f"→ {clean_response}")

    def _format_result_summary(self, tool_name: str, result: str) -> str:
        """Format tool result into concise summary."""
        if not result or not isinstance(result, str):
            return ""

        # Limit length and clean up
        summary = result.strip()[:100]
        if len(result) > 100:
            summary += "..."

        return summary

    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for CLI display."""
        if not text:
            return ""

        # Remove code blocks
        text = re.sub(r"```[^`]*```", "[code block]", text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove bold/italic
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)

        # Remove headers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        return text.strip()
