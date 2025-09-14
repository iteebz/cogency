"""Context assembly for conversations."""

import json

from ..lib.storage import save_message
from ..lib.tokens import count_tokens
from .constants import CONTEXT_LIMITS
from .conversation import current_cycle_messages, history
from .profile import format as profile_format
from .profile import learn
from .system import prompt as system_prompt


def _get_context_limit(model: str) -> int:
    return CONTEXT_LIMITS.get(model, 6400)  # Conservative default


def _truncate_history(history_content: str, max_tokens: int, model: str) -> str:
    """Truncate history content to fit within token budget, preserving most recent messages."""
    if not history_content or max_tokens <= 0:
        return ""

    # Split by lines and truncate from the beginning (preserve most recent)
    lines = history_content.split("\n")
    truncated_lines = []
    current_tokens = 0

    # Work backwards from most recent messages
    for line in reversed(lines):
        line_tokens = count_tokens(line + "\n", model)
        if current_tokens + line_tokens > max_tokens:
            break
        truncated_lines.insert(0, line)  # Preserve original order
        current_tokens += line_tokens

    result = "\n".join(truncated_lines)
    if len(truncated_lines) < len(lines):
        # Add truncation indicator
        result = "[...conversation truncated...]\n" + result

    return result


class Context:

    async def record(self, conversation_id: str, user_id: str, events: list) -> None:
        """Batch record events to storage with chronological ordering. Raises on failure."""
        for event in events:
            timestamp = event.get("timestamp")
            content = event.get("content", "")
            event_type = event["type"]

            # Serialize complex event content
            if event_type == "call":
                content = json.dumps(event["calls"])
            elif event_type == "result":
                content = json.dumps(event["results"])

            await save_message(
                conversation_id, user_id, event_type, content, base_dir=None, timestamp=timestamp
            )

    async def assemble(
        self,
        query: str,
        user_id: str,
        conversation_id: str,
        config=None,
    ) -> list:
        """Assemble context with intelligent token limits to prevent model window overflow.

        Stateless architecture: rebuild complete agent context from storage every cycle.
        No retained state. Pure functional execution. Perfect reproducibility."""

        # Config is config - no agent wrapper bullshit
        tools = config.tools if config else None

        # Get model for token counting and limits
        model = config.llm.llm_model if config else "unknown"
        context_limit = _get_context_limit(model)

        # Build system message components with size tracking
        system_sections = []
        total_tokens = 0

        # Core instructions and tools (protected - always included)
        core_prompt = system_prompt(
            tools=tools, instructions=config.instructions if config else None, include_security=True
        )
        core_tokens = count_tokens(core_prompt, model)
        system_sections.append(core_prompt)
        total_tokens += core_tokens

        # Reserve tokens for user query and current cycle

        query_tokens = count_tokens(query, model)
        current_cycle_tokens = 0
        if config and config.mode != "replay":
            current_cycle = await current_cycle_messages(conversation_id)
            if current_cycle:
                current_cycle_content = "\n".join(msg["content"] for msg in current_cycle)
                current_cycle_tokens = count_tokens(current_cycle_content, model)

        # Reserve 1000 tokens for generation headroom
        reserved_tokens = query_tokens + current_cycle_tokens + 1000
        available_tokens = context_limit - total_tokens - reserved_tokens

        # Add optional context within remaining budget
        if available_tokens > 0:
            # User profile (high priority - user-specific context)
            profile = config.profile if config else True
            if profile and available_tokens > 100:  # Minimum viable profile space
                profile_content = await profile_format(user_id)
                if profile_content:
                    profile_tokens = count_tokens(f"USER CONTEXT:\n{profile_content}", model)
                    if profile_tokens <= available_tokens:
                        system_sections.append("USER CONTEXT:")
                        system_sections.append(profile_content)
                        total_tokens += profile_tokens
                        available_tokens -= profile_tokens

            # Conversation history (medium priority - truncate intelligently if needed)
            if available_tokens > 200:  # Minimum viable history space
                history_content = await history(conversation_id)
                if history_content:
                    history_section = f"CONVERSATION HISTORY:\n{history_content}"
                    history_tokens = count_tokens(history_section, model)

                    if history_tokens <= available_tokens:
                        system_sections.append("CONVERSATION HISTORY:")
                        system_sections.append(history_content)
                        total_tokens += history_tokens
                        available_tokens -= history_tokens
                    else:
                        # Truncate history to fit budget
                        truncated_history = _truncate_history(
                            history_content, available_tokens - 50, model
                        )  # Reserve 50 for header
                        if truncated_history:
                            system_sections.append("CONVERSATION HISTORY:")
                            system_sections.append(truncated_history)

        # Task boundary (always included)
        task_boundary = (
            "CURRENT TASK: Execute the following request independently. "
            "Previous responses are context only - do not assume prior completion."
        )
        system_sections.append(task_boundary)

        # Assemble final messages
        full_system_content = "\n\n".join(system_sections)

        messages = [
            {"role": "system", "content": full_system_content},
            {"role": "user", "content": query},
        ]

        # Add current cycle messages for resume mode continuity (skip in replay mode)
        if config and config.mode != "replay":
            current_cycle = current_cycle_messages(conversation_id)
            messages.extend(current_cycle)

        return messages

    def learn(self, user_id: str, llm) -> None:
        """Trigger profile learning (fire and forget)."""
        learn(user_id, llm)


# Singleton instance
context = Context()
