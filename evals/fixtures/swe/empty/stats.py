def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    # Bug: doesn't handle empty list case
    return total / len(numbers)


def calculate_median(numbers):
    """Calculate median (not affected by the bug)."""
    if not numbers:
        return None

    sorted_nums = sorted(numbers)
    n = len(sorted_nums)

    if n % 2 == 0:
        return (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
    else:
        return sorted_nums[n // 2]
