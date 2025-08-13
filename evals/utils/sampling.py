"""Systematic sampling utilities for authentic benchmarks."""

import random
from typing import Any

import numpy as np


class BenchmarkSampler:
    """Systematic sampling for authentic benchmark datasets."""

    def __init__(self, random_seed: int = 42):
        """Initialize sampler with fixed seed for reproducibility."""
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)

    def stratified_sample(
        self, dataset: list[dict[str, Any]], sample_size: int, stratify_by: str = None
    ) -> list[dict[str, Any]]:
        """
        Stratified sampling to ensure representative distribution.

        Args:
            dataset: Full dataset to sample from
            sample_size: Target sample size
            stratify_by: Field to stratify by (e.g., 'difficulty', 'repo')

        Returns:
            Representative sample from dataset
        """
        if not stratify_by or stratify_by not in dataset[0]:
            # Simple random sampling if no stratification field
            return random.sample(dataset, min(sample_size, len(dataset)))

        # Group by stratification field
        strata = {}
        for item in dataset:
            key = item[stratify_by]
            if key not in strata:
                strata[key] = []
            strata[key].append(item)

        # Calculate proportional sample sizes
        total_items = len(dataset)
        sample = []

        for _stratum_key, stratum_items in strata.items():
            stratum_proportion = len(stratum_items) / total_items
            stratum_sample_size = max(1, int(sample_size * stratum_proportion))

            # Sample from this stratum
            stratum_sample = random.sample(
                stratum_items, min(stratum_sample_size, len(stratum_items))
            )
            sample.extend(stratum_sample)

        # If we're under target, randomly add more
        if len(sample) < sample_size:
            remaining = [item for item in dataset if item not in sample]
            additional_needed = min(sample_size - len(sample), len(remaining))
            sample.extend(random.sample(remaining, additional_needed))

        # If we're over target, randomly remove
        if len(sample) > sample_size:
            sample = random.sample(sample, sample_size)

        return sample

    def difficulty_balanced_sample(
        self, dataset: list[dict[str, Any]], sample_size: int, difficulty_field: str = "difficulty"
    ) -> list[dict[str, Any]]:
        """
        Sample with balanced difficulty distribution.

        Ensures representation across easy/medium/hard categories.
        """
        return self.stratified_sample(dataset, sample_size, difficulty_field)

    def temporal_sample(
        self, dataset: list[dict[str, Any]], sample_size: int, date_field: str = "created_at"
    ) -> list[dict[str, Any]]:
        """
        Sample with temporal distribution to avoid recency bias.
        """
        if date_field not in dataset[0]:
            return random.sample(dataset, min(sample_size, len(dataset)))

        # Sort by date and take systematic sample
        sorted_dataset = sorted(dataset, key=lambda x: x[date_field])
        step = len(sorted_dataset) // sample_size

        if step <= 1:
            return sorted_dataset[:sample_size]

        sample = []
        for i in range(0, len(sorted_dataset), step):
            if len(sample) < sample_size:
                sample.append(sorted_dataset[i])

        return sample[:sample_size]


def validate_sample_quality(
    original_dataset: list[dict[str, Any]], sample: list[dict[str, Any]], stratify_field: str = None
) -> dict[str, Any]:
    """
    Validate that sample maintains statistical properties of original.

    Returns quality metrics for sample validation.
    """
    metrics = {
        "sample_size": len(sample),
        "original_size": len(original_dataset),
        "sample_ratio": len(sample) / len(original_dataset),
    }

    if stratify_field and stratify_field in original_dataset[0]:
        # Compare distributions
        original_dist = {}
        sample_dist = {}

        for item in original_dataset:
            key = item[stratify_field]
            original_dist[key] = original_dist.get(key, 0) + 1

        for item in sample:
            key = item[stratify_field]
            sample_dist[key] = sample_dist.get(key, 0) + 1

        # Calculate distribution similarity
        distribution_error = 0
        for key in original_dist:
            original_prop = original_dist[key] / len(original_dataset)
            sample_prop = sample_dist.get(key, 0) / len(sample)
            distribution_error += abs(original_prop - sample_prop)

        metrics["distribution_error"] = distribution_error
        metrics["original_distribution"] = original_dist
        metrics["sample_distribution"] = sample_dist

    return metrics
