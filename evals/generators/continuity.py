"""Continuity test generators - cross-session information persistence."""

import random


def continuity(size: int = 20) -> list[dict]:
    """Generate cross-session continuity tests."""
    scenarios = [
        ("Remember: My project is called {}", "What was my project called?"),
        ("Store this: API key is {}", "What's the stored API key?"),
        ("Note: Meeting scheduled for {}", "When is the meeting?"),
        ("Save: Database password is {}", "What's the database password?"),
    ]

    projects = ["Phoenix", "Apollo", "Genesis", "Titan"]
    keys = ["abc123", "xyz789", "key456", "token999"]
    times = ["3pm Monday", "2pm Friday", "9am Tuesday", "4pm Thursday"]
    passwords = ["secure123", "pass456", "db789", "auth999"]

    values = [projects, keys, times, passwords]

    return [
        {
            "store_prompt": scenario[0].format(random.choice(values[i % 4])),
            "recall_prompt": scenario[1],
            "criteria": "Correctly recalled specific stored information across conversation turns",
        }
        for i, scenario in enumerate(random.choices(scenarios, k=size))
    ]
