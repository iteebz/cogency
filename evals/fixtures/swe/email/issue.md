# Issue: Add input validation to email parser

**Problem:** The `parse_email` function accepts any string input without validation, leading to runtime errors when processing malformed emails.

**Requirements:**
1. Add validation to check if input is a valid email format
2. Return `None` for invalid emails instead of crashing
3. Keep existing functionality for valid emails

**Test cases:**
- `parse_email("user@domain.com")` → `{"user": "user", "domain": "domain.com"}`
- `parse_email("invalid-email")` → `None`
- `parse_email("")` → `None`

**Files affected:** `email_parser.py`