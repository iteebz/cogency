# Issue: Off-by-one error in array indexing

**Problem:** The `get_last_n_items` function returns one fewer item than requested due to an off-by-one error in the slicing logic.

**Steps to reproduce:**
1. Call `get_last_n_items([1, 2, 3, 4, 5], 3)`
2. Expected: `[3, 4, 5]`
3. Actual: `[4, 5]`

**Expected behavior:** Function should return exactly n items from the end of the list.

**Files affected:** `utils.py`