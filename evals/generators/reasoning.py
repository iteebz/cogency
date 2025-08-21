"""Reasoning test generators - multi-step workflow evaluation."""

import random


def reasoning(size: int = 20) -> list[dict]:
    """Generate multi-step reasoning tests with expanded complexity metadata."""
    workflows = [
        # Simple workflows (1-2 tools, linear) - FORCE tool usage with explicit commands
        (
            "EXECUTE: file_write filename='test.py' content=\"print('hello')\". THEN EXECUTE: shell command='python test.py'",
            "simple",
        ),
        (
            "EXECUTE: file_write filename='num.txt' content='42'. THEN EXECUTE: file_read filename='num.txt'",
            "simple",
        ),
        (
            "EXECUTE: file_write filename='data.txt' content='test'. THEN EXECUTE: file_read filename='data.txt'. THEN EXECUTE: shell command='rm data.txt'",
            "simple",
        ),
        (
            "EXECUTE: shell command='python -c \"print(7*8)\"'. THEN EXECUTE: file_write filename='calc.txt' with the result",
            "simple",
        ),
        # Medium workflows (3-5 tools, some branching)
        (
            "EXECUTE: file_write filename='numbers.txt' content='1,2,3'. THEN EXECUTE: file_read filename='numbers.txt'. THEN EXECUTE: shell command='python -c \"print(sum([1,2,3]))'\"",
            "medium",
        ),
        (
            "EXECUTE: file_write filename='add.py' content='print(10+15)'. THEN EXECUTE: shell command='python add.py'. THEN display the output",
            "medium",
        ),
        (
            "EXECUTE: file_write filename='config.json' content='{\"name\":\"John\", \"age\":20}'. THEN EXECUTE: file_read filename='config.json'. THEN modify age to 25 and save back",
            "medium",
        ),
        (
            "EXECUTE: file_write filename='nums.txt' content='1\\n2\\n3\\n4\\n5'. THEN EXECUTE: file_read filename='nums.txt'. THEN EXECUTE: shell command to find maximum",
            "medium",
        ),
        (
            "EXECUTE: file_write filename='shopping.txt' content='apple,banana,cherry'. THEN EXECUTE: file_read filename='shopping.txt'. THEN sort and count items",
            "medium",
        ),
        # Complex workflows (6+ tools, conditional logic, error handling)
        (
            "EXECUTE: shell command='mkdir workspace'. THEN EXECUTE: file_write filename='workspace/readme.txt' content='Hello'. THEN EXECUTE: file_list path='workspace'. THEN EXECUTE: shell command='rm -rf workspace'",
            "complex",
        ),
        (
            "EXECUTE: shell command='mkdir project'. THEN EXECUTE: file_write filename='project/README.md' content='# Project'. THEN EXECUTE: file_list path='project'. THEN EXECUTE: shell command='rm -rf project'",
            "complex",
        ),
        (
            "EXECUTE: file_write filename='people.csv' content='name,age\\nJohn,25\\nJane,30\\nBob,35'. THEN EXECUTE: file_read filename='people.csv'. THEN calculate average age with python",
            "complex",
        ),
        (
            "EXECUTE: file_write filename='timer.txt' content='5'. THEN append '4,3,2,1' separately. THEN EXECUTE: file_read filename='timer.txt' to show final countdown",
            "complex",
        ),
        (
            "EXECUTE: file_list to check if 'backup.txt' exists. IF missing, EXECUTE: file_write filename='backup.txt' with current timestamp",
            "complex",
        ),
        (
            "EXECUTE: file_write filename='log.txt' content='Entry 1'. THEN append 2 more entries with timestamps. THEN count lines and archive if >2",
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
