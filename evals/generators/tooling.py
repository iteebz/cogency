"""Tooling test generators - appropriate tool selection and orchestration."""

import random


def tooling(size: int = 20) -> list[dict]:
    """Generate tool selection and orchestration tests with EXPLICIT tool requirements."""
    scenarios = [
        (
            "EXECUTE: file_write filename='{}' content='{}'",
            "Actually used file_write tool to create file",
        ),
        ("EXECUTE: shell command='echo {}'", "Actually used shell tool to run echo command"),
        (
            "EXECUTE: file_list to show all files in current directory",
            "Actually used file_list tool to list files",
        ),
        (
            "EXECUTE: shell command='python -c \"print({})\"'",
            "Actually used shell tool for Python execution",
        ),
        (
            "EXECUTE: search query='Python asyncio tutorial'. THEN summarize the findings from search results",
            "Actually used search tool and provided summary",
        ),
        (
            "EXECUTE: scrape url='https://httpbin.org/html'. THEN analyze the scraped content",
            "Actually used scrape tool and analyzed content",
        ),
        (
            "EXECUTE: search query='latest AI news'. THEN EXECUTE: file_write filename='ai_summary.txt' with key findings",
            "Actually used search tool then file_write tool in sequence",
        ),
    ]

    words = ["hello", "test", "data", "output"]
    files = ["temp.txt", "test.txt", "output.txt"]
    numbers = ["42", "123", "7*8"]

    return [
        {
            "prompt": scenario[0].format(
                random.choice(files) if "{}" in scenario[0] else "",
                random.choice(words)
                if "{}" in scenario[0] and "echo" in scenario[0]
                else random.choice(numbers),
            ),
            "criteria": scenario[1],
        }
        for scenario in random.choices(scenarios, k=size)
    ]
