"""User memory management - clean and minimal."""

from typing import Any, Optional

from ..lib.storage import load_memory, save_memory


class UserMemory:
    """User-scoped profile and preference management."""

    def format(self, user_id: str) -> str:
        """Format user memory for context display."""
        try:
            memory = self.get(user_id)
            if not memory:
                return ""

            import json

            return f"User context:\n{json.dumps(memory, indent=2)}"
        except Exception:
            return ""

    def get(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user memory data."""
        if user_id is None:
            raise ValueError("user_id cannot be None")
        try:
            return load_memory(user_id)
        except Exception:
            return None

    def update(self, user_id: str, memory_data: dict[str, Any]) -> bool:
        """Update user memory data."""
        if user_id is None:
            return False
        try:
            save_memory(user_id, memory_data)
            return True
        except Exception:
            return False

    async def learn(
        self, user_id: str, query: str, response: str, llm=None, embedder=None, observer=None
    ) -> None:
        """Learn from user interaction."""
        if observer:
            observer.event(
                "memory_learn_start",
                {
                    "user_id": user_id,
                    "has_llm": llm is not None,
                    "query_length": len(query) if query else 0,
                    "response_length": len(response) if response else 0,
                },
            )

        if not user_id or user_id == "default" or not llm:
            if observer:
                observer.event(
                    "memory_learn_skip", {"reason": f"user_id={user_id}, has_llm={llm is not None}"}
                )
            return

        try:
            current = self.get(user_id) or {}

            if observer:
                observer.event("memory_current_profile", {"current": current})

            extraction_prompt = f"""Extract updated user profile from this interaction.

Current profile: {current}

User query: {query}
Agent response: {response[:800]}

Extract user profile with exactly these 4 fields:
- name: What to call them (if mentioned or can infer, otherwise keep existing)
- projects: Current projects they're working on (list of strings)
- interests: Technical topics/technologies they use (list of strings)
- notes: Free-form observations about their working style, preferences, context (max 200 chars)

Return ONLY valid JSON with these 4 fields. Do not use code blocks or markdown formatting. Return raw JSON only."""

            if observer:
                observer.event("memory_llm_request", {"prompt_length": len(extraction_prompt)})

            result = await llm.generate([{"role": "user", "content": extraction_prompt}])

            if result.success:
                raw_response = result.unwrap().strip()
                if observer:
                    observer.event("memory_llm_response", {"response": raw_response})

                import json

                try:
                    updated = json.loads(raw_response)
                    if isinstance(updated, dict) and all(
                        field in updated for field in ["name", "projects", "interests", "notes"]
                    ):
                        if observer:
                            observer.event("memory_update_success", {"updated": updated})
                        self.update(user_id, updated)
                    else:
                        if observer:
                            observer.event(
                                "memory_validation_failed",
                                {
                                    "missing_fields": [
                                        f
                                        for f in ["name", "projects", "interests", "notes"]
                                        if f not in updated
                                    ]
                                },
                            )
                except json.JSONDecodeError as e:
                    if observer:
                        observer.event(
                            "memory_json_parse_failed", {"error": str(e), "response": raw_response}
                        )
            else:
                if observer:
                    observer.event("memory_llm_failed", {"error": result.error})

        except Exception as e:
            # Memory updates never block - graceful degradation
            if observer:
                observer.event("memory_learn_exception", {"error": str(e)})
            pass

    def clear(self, user_id: str) -> bool:
        """Clear user memory data."""
        if user_id is None:
            return False
        return self.update(user_id, {})


# Singleton instance
memory = UserMemory()
