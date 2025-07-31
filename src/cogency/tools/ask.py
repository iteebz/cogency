import logging
from dataclasses import dataclass
from typing import Any, Dict

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class AskArgs:
    prompt: str


@tool
class Ask(Tool):
    """Pauses execution and asks for explicit user confirmation before proceeding."""

    def __init__(self):
        super().__init__(
            name="ask",
            description="Ask for user confirmation before executing a high-stakes or destructive action.",
            schema="ask(prompt: str)",
            emoji="🤔",
            params=AskArgs,
            examples=[
                "ask(prompt='I am about to run `rm -rf /`. Proceed?')",
                "ask(prompt='This will overwrite the existing file `config.json`. Continue?')",
            ],
            rules=[
                "CRITICAL: Use this tool BEFORE any potentially irreversible action (deleting files, running installs, etc.).",
                "The prompt must be a clear, direct yes/no question.",
                "If the user denies, you MUST stop the current plan and rethink your approach.",
            ],
        )

    async def run(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Prompt the user for confirmation."""
        try:
            # Print the prompt in a clear, attention-grabbing way.
            print(f"\n{'='*20}\nACTION REQUIRED\n{'='*20}")
            print(f"{self.emoji} {prompt} (yes/no)")

            # Get user input directly.
            response = input("> ").lower().strip()

            if response in ["yes", "y"]:
                print("✅ User approved. Continuing...")
                return Result.ok({"approved": True, "response": "User approved."})
            else:
                print("❌ User denied. Aborting current task.")
                return Result.fail("User denied the action.")

        except Exception as e:
            logger.error(f"Ask tool failed: {e}")
            return Result.fail(f"Failed to get user confirmation: {str(e)}")
