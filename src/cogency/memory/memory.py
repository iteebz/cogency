"""Pure LLM-native memory architecture.

Memory = LLM + Recent Interactions + User Impression + Synthesis

Zero external dependencies. Zero ceremony. Maximum elegance.
"""


class Memory:
    """LLM-native memory system - user impression through reasoning."""

    def __init__(self, llm, store=None, user_id="default"):
        self.llm = llm
        self.store = store
        self.user_id = user_id
        self.recent = ""  # Raw recent interactions
        self.impression = ""  # Synthesized user impression
        self.synthesis_threshold = 16000

    async def remember(self, content: str, human: bool = False) -> None:
        """Remember information with human weighting."""
        weight = "[HUMAN]" if human else "[AGENT]"
        self.recent += f"\n{weight} {content}"

        if len(self.recent) > self.synthesis_threshold:
            await self._synthesize()

    async def recall(self) -> str:
        """Recall impression context for reasoning."""
        if not self.impression and not self.recent:
            return ""

        context = ""
        if self.impression:
            context += f"USER IMPRESSION:\n{self.impression}\n\n"
        if self.recent:
            context += f"RECENT INTERACTIONS:\n{self.recent}\n\n"

        return context

    async def _synthesize(self) -> None:
        """LLM-driven impression synthesis."""
        if not self.recent.strip():
            return

        prompt = f"""Form a refined impression of this user based on their interactions:

Current Impression: {self.impression}
Recent Interactions: {self.recent}

Create a cohesive user impression that:
- Captures essential preferences, goals, and context
- Prioritizes human statements over agent observations
- Builds understanding over time rather than just facts
- Eliminates contradictions and redundancy
- Maintains personal context and behavioral patterns

Refined Impression:"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        if result.success:
            self.impression = result.data
        else:
            # Fallback - keep existing impression if synthesis fails
            pass
        self.recent = ""

        # Auto-save after synthesis
        await self.save()

    async def save(self) -> bool:
        """Save memory to persistent store."""
        if not self.store:
            return False

        memory_key = f"memory:{self.user_id}"

        # Create a minimal state-like object for the Store interface
        from dataclasses import dataclass

        @dataclass
        class MemoryState:
            recent: str
            impression: str

        memory_state = MemoryState(recent=self.recent, impression=self.impression)

        return await self.store.save(memory_key, memory_state)

    async def load(self) -> bool:
        """Load memory from persistent store."""
        if not self.store:
            return False

        memory_key = f"memory:{self.user_id}"
        data = await self.store.load(memory_key)

        if data and "state" in data:
            state_data = data["state"]
            self.recent = state_data.get("recent", "")
            self.impression = state_data.get("impression", "")
            return True

        return False
