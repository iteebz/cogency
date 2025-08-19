"""Reasoning test generators - multi-step workflow evaluation."""

import random


def reasoning(size: int = 20) -> list[dict]:
    """Generate multi-step reasoning tests with complexity metadata."""
    workflows = [
        # Simple workflows (basic file operations)
        ("Create 'test.py', write print('hello'), run it, then delete the file", "simple"),
        ("Create file 'data.txt' with 'test', read it, then delete the file", "simple"),
        # Medium workflows (calculations + file operations)
        (
            "Create file 'numbers.txt' with '1,2,3', read it, calculate sum, display result",
            "medium",
        ),
        ("Write Python script to add two numbers, execute it with inputs 5 and 7", "medium"),
        # Complex workflows (directory operations + orchestration)
        ("Make directory 'temp', create file inside it, list contents, then clean up", "complex"),
        ("Create directory 'project', add README.md, list structure, remove everything", "complex"),
    ]

    tests = []
    for _ in range(size):
        workflow, complexity = random.choice(workflows)
        tests.append(
            {
                "prompt": workflow,
                "criteria": "Completed multi-step workflow using appropriate tools in logical sequence",
                "complexity": complexity,
            }
        )

    return tests
