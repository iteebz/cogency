"""Test sampling utilities - canonical distribution strategies."""

import random
from collections import defaultdict
from typing import Any, Callable


def stratified_sample(
    templates: list[Any], size: int, generator_fn: Callable[[Any], dict]
) -> list[dict]:
    """Stratified sampling with balanced difficulty distribution.

    Args:
        templates: List of templates/patterns to sample from
        size: Target sample size
        generator_fn: Function that converts template to test dict

    Returns:
        List of test dictionaries with balanced distribution
    """
    tests = []
    templates_per_stratum = max(1, size // len(templates))

    # Ensure each template gets represented
    for template in templates:
        stratum_size = min(templates_per_stratum, size - len(tests))
        if stratum_size <= 0:
            break

        for _ in range(stratum_size):
            tests.append(generator_fn(template))

    # Fill remaining slots with random selection
    while len(tests) < size:
        template = random.choice(templates)
        tests.append(generator_fn(template))

    # Shuffle to avoid systematic ordering effects
    random.shuffle(tests)
    return tests


def stratify_by_difficulty(tests: list[dict], target_size: int) -> list[dict]:
    """Core-level stratified sampling based on test difficulty metadata.

    Args:
        tests: List of test dictionaries with difficulty/complexity metadata
        target_size: Target sample size

    Returns:
        Stratified sample with balanced difficulty distribution
    """
    # Group tests by difficulty
    difficulty_groups = defaultdict(list)
    for test in tests:
        # Support both 'difficulty' and 'complexity' field names
        difficulty = test.get("difficulty", test.get("complexity", "medium"))
        difficulty_groups[difficulty].append(test)

    if not difficulty_groups:
        # No difficulty metadata, return random sample
        return random.sample(tests, min(target_size, len(tests)))

    # Calculate target per difficulty level
    difficulties = list(difficulty_groups.keys())
    per_difficulty = max(1, target_size // len(difficulties))

    stratified_tests = []

    # Sample from each difficulty level
    for difficulty in difficulties:
        available = difficulty_groups[difficulty]
        sample_size = min(per_difficulty, len(available), target_size - len(stratified_tests))

        if sample_size > 0:
            stratified_tests.extend(random.sample(available, sample_size))

    # Fill remaining slots if needed
    remaining_tests = [t for t in tests if t not in stratified_tests]
    while len(stratified_tests) < target_size and remaining_tests:
        stratified_tests.append(remaining_tests.pop(random.randint(0, len(remaining_tests) - 1)))

    # Shuffle final selection
    random.shuffle(stratified_tests)
    return stratified_tests[:target_size]


def uniform_sample(
    templates: list[Any], size: int, generator_fn: Callable[[Any], dict]
) -> list[dict]:
    """Uniform random sampling - original behavior."""
    return [generator_fn(random.choice(templates)) for _ in range(size)]
