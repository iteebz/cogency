# Issue: Optimize duplicate detection algorithm

**Problem:** The `find_duplicates` function has O(n²) time complexity, causing performance issues with large datasets.

**Current behavior:** Uses nested loops to compare every element with every other element.

**Requirements:**
1. Optimize to O(n) time complexity using appropriate data structure
2. Maintain same return format: list of duplicate values (not indices)
3. Preserve order of first occurrence for duplicates

**Performance target:** Should handle 10,000+ items efficiently

**Files affected:** `algorithms.py`