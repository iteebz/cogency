"""Pure LLM-native memory architecture.

Memory = LLM + Recent Interactions + User Impression + Synthesis

Zero external dependencies. Zero ceremony. Maximum elegance.
"""


class Memory:
    """LLM-native memory system - user impression through reasoning."""

    def __init__(self, llm):
        self.llm = llm
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

        self.impression = await self.llm.complete(prompt)
        self.recent = ""
