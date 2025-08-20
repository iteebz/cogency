"""Tooling test generators - appropriate tool selection and orchestration."""

import random


def tooling(size: int = 20) -> list[dict]:
    """Generate tool selection and orchestration tests."""
    scenarios = [
        ("Create file '{}' with content '{}'", "Used appropriate tool for file creation"),
        ("Run command 'echo {}'", "Used shell tool appropriately"),
        ("List files in current directory", "Selected appropriate tool for file listing"),
        ("Execute 'python -c \"print({})\"'", "Used shell for Python execution"),
        (
            "Search for 'Python asyncio tutorial' and summarize findings",
            "Used search tool and provided summary",
        ),
        (
            "Scrape content from https://httpbin.org/html and analyze",
            "Used scrape tool and analyzed content",
        ),
        (
            "Search for latest news about AI and create summary file",
            "Used search tool then file creation tool",
        ),
    ]

    words = ["hello", "test", "data", "output"]
    files = ["temp.txt", "test.txt", "output.txt"]

    return [
        {
            "prompt": scenario[0].format(
                random.choice(files) if "{}" in scenario[0] else "", random.choice(words)
            ),
            "criteria": scenario[1],
        }
        for scenario in random.choices(scenarios, k=size)
    ]
