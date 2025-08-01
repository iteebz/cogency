# Issue: Handle empty list edge case in statistics calculator

**Problem:** The `calculate_average` function crashes with a division by zero error when given an empty list.

**Steps to reproduce:**
1. Call `calculate_average([])`
2. Results in: `ZeroDivisionError: division by zero`

**Expected behavior:** Should return `None` or `0` for empty lists instead of crashing.

**Additional context:** This function is used in data processing pipelines where empty datasets are possible.

**Files affected:** `stats.py`