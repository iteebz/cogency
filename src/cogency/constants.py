MAX_TOKENS = 16384  # Increased for complex multi-tool reasoning
MAX_TOOL_CALLS_PER_ITERATION = 3  # Limit to prevent JSON parsing issues

# Feature flags
ADAPT_REACT = False  # Disable mode switching for debugging

# Memory limits
MAX_ITERATIONS_HISTORY = 5
MAX_FAILURES_HISTORY = 5
DEFAULT_MAX_ITERATIONS = 3  # Low limit for debugging recursion
RECURSION_LIMIT = 3  # Hard limit for testing

# Response context limits
RESPOND_MAX_ITERATIONS = 3  # Number of recent iterations to include in final response
RESPOND_MAX_RESULT_LENGTH = 200  # Max chars per iteration result (TODO: replace with LLM compression)
