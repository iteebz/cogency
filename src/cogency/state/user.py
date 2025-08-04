"""User profile data structure."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class UserProfile:
    """Persistent user understanding - builds over time."""

    user_id: str

    # Core Understanding
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise: List[str] = field(default_factory=list)
    communication_style: str = ""

    # Contextual Knowledge
    projects: Dict[str, str] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Interaction Patterns
    success_patterns: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    synthesis_version: int = 1

    def update(self, interaction_insights: Dict[str, Any]) -> None:
        """Update profile from interaction insights."""
        self.update_from_interaction(interaction_insights)

    def update_from_interaction(self, interaction_insights: Dict[str, Any]) -> None:
        """Update profile from interaction insights."""
        self.interaction_count += 1
        self.last_updated = datetime.now()

        # Update preferences
        if "preferences" in interaction_insights:
            self.preferences.update(interaction_insights["preferences"])

        # Add new goals (bounded)
        if "goals" in interaction_insights:
            for goal in interaction_insights["goals"]:
                if goal not in self.goals:
                    self.goals.append(goal)
            if len(self.goals) > 10:
                self.goals = self.goals[-10:]

        # Update expertise areas
        if "expertise" in interaction_insights:
            for area in interaction_insights["expertise"]:
                if area not in self.expertise:
                    self.expertise.append(area)
            if len(self.expertise) > 15:
                self.expertise = self.expertise[-15:]

        # Update communication style
        if "communication_style" in interaction_insights:
            self.communication_style = interaction_insights["communication_style"]

        # Update project context
        if "project_context" in interaction_insights:
            self.projects.update(interaction_insights["project_context"])
            if len(self.projects) > 10:
                # Keep most recent projects
                items = list(self.projects.items())[-10:]
                self.projects = dict(items)

        # Track success/failure patterns
        if "success_pattern" in interaction_insights:
            pattern = interaction_insights["success_pattern"]
            if pattern and pattern not in self.success_patterns:
                self.success_patterns.append(pattern)
                if len(self.success_patterns) > 5:
                    self.success_patterns = self.success_patterns[-5:]

        if "failure_pattern" in interaction_insights:
            pattern = interaction_insights["failure_pattern"]
            if pattern and pattern not in self.failure_patterns:
                self.failure_patterns.append(pattern)
                if len(self.failure_patterns) > 5:
                    self.failure_patterns = self.failure_patterns[-5:]
