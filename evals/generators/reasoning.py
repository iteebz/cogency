"""Reasoning test generators - multi-step workflow evaluation."""

import random


def reasoning(size: int = 20) -> list[dict]:
    """Generate multi-step reasoning tests with expanded complexity metadata."""
    workflows = [
        # Simple workflows (1-2 tools, linear) - FORCE tool usage with "USE:" commands
        (
            "Create file 'test.py' with content print('hello'). Then execute the file using shell command.",
            "simple",
        ),
        (
            "Use file_write to save number 42 to 'num.txt', then use file_read to verify it",
            "simple",
        ),
        (
            "Create 'data.txt' with content 'test' using file_write, read with file_read, delete with shell",
            "simple",
        ),
        ("Use shell command to calculate 7 * 8 with python -c, save output to file", "simple"),
        # Medium workflows (3-5 tools, some branching)
        (
            "Write '1,2,3' to numbers.txt, read the file, calculate sum with python, display result",
            "medium",
        ),
        ("Create Python addition script, write to file, execute with shell, show output", "medium"),
        (
            "Create config.json with {name:'John', age:20}, read file, modify age to 25, write back",
            "medium",
        ),
        (
            "Write numbers 1-5 to file (one per line), read file, find maximum using python",
            "medium",
        ),
        (
            "Create shopping.txt with 'apple,banana,cherry', read file, sort items, count total",
            "medium",
        ),
        # Complex workflows (6+ tools, conditional logic, error handling)
        (
            "Create directory 'workspace', add file 'readme.txt' inside, list directory, clean up",
            "complex",
        ),
        (
            "Make 'project' folder, create 'README.md' with content, list structure, remove all",
            "complex",
        ),
        (
            "Create CSV file with name,age rows for 3 people, read CSV, calculate average age",
            "complex",
        ),
        (
            "Create timer.txt, write countdown 5,4,3,2,1 (separate writes), read final count",
            "complex",
        ),
        (
            "Check if 'backup.txt' exists with file_list, if missing create with timestamp",
            "complex",
        ),
        (
            "Create log.txt, append 3 entries with timestamps, count lines, archive if >2 lines",
            "complex",
        ),
    ]

    tests = []
    for _ in range(size):
        workflow, complexity = random.choice(workflows)
        tests.append(
            {
                "prompt": workflow,
                "criteria": "Actually executed required tools (file_write, file_read, shell) in logical sequence to complete workflow",
                "complexity": complexity,
            }
        )

    return tests
