"""Profile compression utilities for context injection."""

from cogency.state.user_profile import UserProfile


def compress_for_injection(profile: UserProfile, max_tokens: int = 800) -> str:
    """Generate situated context for agent initialization."""
    sections = []

    if profile.communication_style:
        sections.append(f"COMMUNICATION: {profile.communication_style}")

    if profile.goals:
        goals_str = "; ".join(profile.goals[-3:])
        sections.append(f"CURRENT GOALS: {goals_str}")

    if profile.preferences:
        prefs_items = list(profile.preferences.items())[-5:]
        prefs_str = ", ".join(f"{k}: {v}" for k, v in prefs_items)
        sections.append(f"PREFERENCES: {prefs_str}")

    if profile.projects:
        projects_items = list(profile.projects.items())[-3:]
        projects_str = "; ".join(f"{k}: {v}" for k, v in projects_items)
        sections.append(f"ACTIVE PROJECTS: {projects_str}")

    if profile.expertise_areas:
        expertise_str = ", ".join(profile.expertise_areas[-5:])
        sections.append(f"EXPERTISE: {expertise_str}")

    if profile.constraints:
        constraints_str = "; ".join(profile.constraints[-3:])
        sections.append(f"CONSTRAINTS: {constraints_str}")

    result = "\n".join(sections)
    return result[:max_tokens] if len(result) > max_tokens else result
