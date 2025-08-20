"""Continuity test generators - cross-session information persistence."""

import random


def continuity(size: int = 20) -> list[dict]:
    """Generate cross-session continuity tests."""
    scenarios = [
        ("Remember: My project is called {}", "What was my project called?"),
        ("Store this: My favorite color is {}", "What's my favorite color?"),
        ("Note: Meeting scheduled for {}", "When is the meeting?"),
        ("Save: My username is {}", "What's my username?"),
    ]

    projects = ["Phoenix", "Apollo", "Genesis", "Titan"]
    colors = ["blue", "green", "red", "purple"]
    times = ["3pm Monday", "2pm Friday", "9am Tuesday", "4pm Thursday"]
    usernames = ["alice123", "bob456", "charlie789", "diana999"]

    values = [projects, colors, times, usernames]

    return [
        {
            "store_prompt": scenario[0].format(random.choice(values[i % 4])),
            "recall_prompt": scenario[1],
            "criteria": "Correctly recalled specific stored information across conversation turns",
        }
        for i, scenario in enumerate(random.choices(scenarios, k=size))
    ]
