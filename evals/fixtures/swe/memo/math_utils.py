def fibonacci(n):
    """Calculate the nth Fibonacci number using naive recursion."""
    if n <= 1:
        return n

    # Inefficient: recalculates same values multiple times
    return fibonacci(n - 1) + fibonacci(n - 2)


def factorial(n):
    """Calculate factorial (not related to the issue)."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
