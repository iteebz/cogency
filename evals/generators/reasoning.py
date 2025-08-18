"""Reasoning test generators - multi-step workflow evaluation."""

import random
from typing import List, Dict


def reasoning(size: int = 20) -> List[Dict]:
    """Generate multi-step reasoning tests."""
    workflows = [
        "Create 'test.py', write print('hello'), run it, then delete the file",
        "Create file 'numbers.txt' with '1,2,3', read it, calculate sum, display result", 
        "Make directory 'temp', create file inside it, list contents, then clean up",
        "Write Python script to add two numbers, execute it with inputs 5 and 7",
    ]
    
    return [
        {
            "prompt": random.choice(workflows),
            "criteria": "Completed multi-step workflow using appropriate tools in logical sequence"
        }
        for _ in range(size)
    ]