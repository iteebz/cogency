# Issue: Add memoization to expensive Fibonacci calculation

**Problem:** The recursive `fibonacci` function recalculates the same values multiple times, leading to exponential time complexity.

**Current behavior:** `fibonacci(30)` takes several seconds due to redundant calculations.

**Requirements:**
1. Add memoization/caching to avoid redundant calculations
2. Maintain the same function signature and return values
3. Should handle edge cases (n=0, n=1) correctly

**Performance target:** `fibonacci(50)` should complete in under 1 second

**Files affected:** `math_utils.py`