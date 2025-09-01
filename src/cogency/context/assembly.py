"""Context assembly for conversations."""

from ..core.protocols import Event
from ..lib.storage import save_message
from .conversation import current_cycle_messages, history
from .profile import format as profile_format
from .profile import learn
from .system import prompt as system_prompt


class Context:
    """Context assembly for streaming conversations."""

    def record(self, conversation_id: str, user_id: str, events: list) -> bool:
        """Batch record events to storage with chronological ordering."""
        import json

        for event in events:
            timestamp = event.get("timestamp")
            content = event.get("content", "")

            match event["type"]:
                case Event.USER:
                    if not save_message(conversation_id, user_id, Event.USER, content, timestamp):
                        return False
                case Event.THINK:
                    if not save_message(conversation_id, user_id, Event.THINK, content, timestamp):
                        return False
                case Event.CALLS:
                    if not save_message(
                        conversation_id, user_id, Event.CALLS, json.dumps(event["calls"]), timestamp
                    ):
                        return False
                case Event.RESULTS:
                    if not save_message(
                        conversation_id,
                        user_id,
                        Event.RESULTS,
                        json.dumps(event["results"]),
                        timestamp,
                    ):
                        return False
                case Event.RESPOND:
                    if not save_message(
                        conversation_id, user_id, Event.RESPOND, content, timestamp
                    ):
                        return False

        return True

    def assemble(
        self,
        query: str,
        user_id: str,
        conversation_id: str,
        tools: list = None,
        config=None,
    ) -> list:
        """Assemble context into single system message + user query format."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        # Build system message with all context
        system_sections = []

        # Core instructions and tools (with optional user instructions)
        instructions = config.instructions if config else None
        system_sections.append(
            system_prompt(tools=tools, instructions=instructions, include_security=True)
        )

        # User profile context
        profile = config.profile if config else True
        if profile:
            profile_content = profile_format(user_id)
            if profile_content:
                system_sections.append("USER CONTEXT:")
                system_sections.append(profile_content)

        # Conversation history (past cycles only)
        history_content = history(conversation_id)
        if history_content:
            system_sections.append("CONVERSATION HISTORY:")
            system_sections.append(history_content)

        # Task boundary to prevent context confusion
        system_sections.append(
            "CURRENT TASK: Execute the following request independently. "
            "Previous responses are context only - do not assume prior completion."
        )

        # Combine all sections into system message
        full_system_content = "\n\n".join(system_sections)

        messages = [
            {"role": "system", "content": full_system_content},
            {"role": "user", "content": query},
        ]

        # Add current cycle messages for replay mode continuity
        current_cycle = current_cycle_messages(conversation_id)
        messages.extend(current_cycle)

        return messages

    def learn(self, user_id: str, llm) -> None:
        """Trigger profile learning (fire and forget)."""
        learn(user_id, llm)


# Singleton instance
context = Context()
