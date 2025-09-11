"""Memory integration tests - REMOVED.

Profile learning integration tests were fundamentally broken because:

1. Profile learning is intentionally disabled in test environments (pytest detection)
2. Tests tried to mock non-existent imports (cogency.context.profile.Gemini)
3. Background async learning makes integration tests non-deterministic

Profile learning is properly tested via unit tests in tests/unit/context/test_profile.py:
- should_learn() logic with message counting and thresholds
- learn_async() logic with LLM generation and profile updating
- Storage integration with isolated temp directories
- Error handling and edge cases

This provides complete coverage of profile learning functionality without the
complexity and brittleness of full integration tests.
"""
