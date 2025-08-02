"""ReasoningContext - Structured cognition without string pollution."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ReasoningContext:
    """Structured reasoning memory - no string-based fields."""

    # Core Cognition (Structured Facts - ChatGPT's requirement)
    goal: str = ""
    facts: Dict[str, Any] = field(default_factory=dict)
    strategy: str = ""
    insights: List[str] = field(default_factory=list)

    # Reasoning History (Simplified - Gemini's requirement)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)

    def add_insight(self, insight: str) -> None:
        """Add new insight with bounded growth."""
        if insight and insight.strip() and insight not in self.insights:
            self.insights.append(insight.strip())
            # Prevent unbounded growth - keep last 10
            if len(self.insights) > 10:
                self.insights = self.insights[-10:]

    def update_facts(self, key: str, value: Any) -> None:
        """Update structured knowledge."""
        if key and key.strip():
            self.facts[key] = value
            # Prevent unbounded growth - keep last 20 facts
            if len(self.facts) > 20:
                oldest_keys = list(self.facts.keys())[:-20]
                for old_key in oldest_keys:
                    del self.facts[old_key]

    def record_thinking(self, thinking: str, tool_calls: List[Dict[str, Any]]) -> None:
        """Record reasoning step."""
        thought = {
            "thinking": thinking,
            "tool_calls": tool_calls,
            "timestamp": datetime.now().isoformat(),
        }
        self.thoughts.append(thought)
        # Keep last 5 thoughts for context
        if len(self.thoughts) > 5:
            self.thoughts = self.thoughts[-5:]

    def compress_for_context(self, max_tokens: int = 1000) -> str:
        """Intelligent compression for LLM context."""
        sections = []

        if self.goal:
            sections.append(f"GOAL: {self.goal}")

        if self.strategy:
            sections.append(f"STRATEGY: {self.strategy}")

        if self.facts:
            # Show most recent facts
            recent_facts = list(self.facts.items())[-5:]
            facts_str = "; ".join(f"{k}: {v}" for k, v in recent_facts)
            sections.append(f"FACTS: {facts_str}")

        if self.insights:
            # Show most recent insights
            recent_insights = self.insights[-3:]
            insights_str = "; ".join(recent_insights)
            sections.append(f"INSIGHTS: {insights_str}")

        if self.thoughts:
            # Show last thought summary
            last_thought = self.thoughts[-1]
            sections.append(f"LAST THINKING: {last_thought['thinking'][:200]}")

        result = "\n".join(sections)
        return result[:max_tokens] if len(result) > max_tokens else result
