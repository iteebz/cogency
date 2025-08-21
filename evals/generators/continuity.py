"""Continuity test generators - TRUE cross-session information persistence."""

import random


def continuity(size: int = 20) -> list[dict]:
    """Generate cross-session continuity tests that test ACTUAL persistence, not conversation memory."""
    scenarios = [
        # Personal information persistence
        (
            "STORE: My project is called {}. Make sure you remember this for future sessions.",
            "What was my project called? (Answer from persistent memory)",
        ),
        (
            "STORE: My preferred programming language is {}. Save this to my persistent profile.",
            "What programming language do I prefer? (Retrieve from memory)",
        ),
        (
            "STORE: My work schedule is {}. Remember this information.",
            "What's my work schedule? (Check persistent memory)",
        ),
        (
            "STORE: My primary goal this quarter is {}. Keep this in mind.",
            "What's my main goal this quarter? (From persistent memory)",
        ),
        # Context and preferences
        (
            "STORE: I'm working on {} technology stack. Remember this context.",
            "What technology am I working with? (From memory)",
        ),
        (
            "STORE: My communication preference is {}. Note this for future interactions.",
            "How do I prefer to communicate? (From stored preferences)",
        ),
        (
            "STORE: My expertise level in Python is {}. Remember this.",
            "What's my Python skill level? (Check memory)",
        ),
        (
            "STORE: My deadline for the main project is {}. Don't forget this.",
            "When is my project deadline? (From persistent memory)",
        ),
        # Temporal persistence tests
        (
            "STORE: Today I completed {}. Add this to my progress log.",
            "What did I complete in my last session? (From memory)",
        ),
        (
            "STORE: My next priority task is {}. Remember for tomorrow.",
            "What was I planning to work on next? (From previous session)",
        ),
    ]

    projects = ["Phoenix AI", "Apollo Dashboard", "Genesis Framework", "Titan Analytics"]
    languages = ["Python", "TypeScript", "Rust", "Go"]
    schedules = [
        "9am-5pm weekdays",
        "flexible hours",
        "remote Tuesdays/Thursdays",
        "morning person",
    ]
    goals = ["launch MVP", "improve performance", "expand user base", "add new features"]
    stacks = ["React/Node.js", "Python/FastAPI", "Rust/WebAssembly", "Go/Docker"]
    communication = [
        "direct feedback",
        "detailed explanations",
        "concise updates",
        "visual examples",
    ]
    expertise = ["intermediate", "advanced", "expert", "learning"]
    deadlines = ["end of month", "next Friday", "Q1 2025", "two weeks"]
    completions = ["user authentication", "database migration", "UI redesign", "performance tests"]
    priorities = ["bug fixes", "documentation", "feature development", "code review"]

    value_sets = [
        projects,
        languages,
        schedules,
        goals,
        stacks,
        communication,
        expertise,
        deadlines,
        completions,
        priorities,
    ]

    return [
        {
            "store_prompt": scenario[0].format(random.choice(value_sets[i % len(value_sets)])),
            "recall_prompt": scenario[1],
            "criteria": "Retrieved correct information from persistent cross-session memory (NOT conversation memory)",
            "test_type": "cross_session_memory",
            "requires_agent_destruction": True,  # Critical flag for test runner
        }
        for i, scenario in enumerate(random.choices(scenarios, k=size))
    ]
