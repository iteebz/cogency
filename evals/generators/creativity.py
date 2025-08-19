"""Creativity test generator - demonstrates extensibility."""

import random


def creativity(size: int = 20) -> list[dict]:
    """Generate creativity evaluation tests."""
    prompts = [
        "Write a haiku about debugging code",
        "Create a metaphor explaining recursion",
        "Invent a new programming language concept",
        "Design a creative solution for code reviews",
    ]

    return [
        {
            "prompt": random.choice(prompts),
            "criteria": "Demonstrated creativity, originality, and coherent expression",
        }
        for _ in range(size)
    ]
