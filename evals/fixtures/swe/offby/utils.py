def get_last_n_items(items, n):
    """Return the last n items from a list."""
    if n <= 0 or not items:
        return []

    # Bug: should be -n, not -(n-1)
    return items[-(n - 1) :]


def helper_function():
    """Helper function that's not related to the bug."""
    return "helper"
