"""Tool configuration constants."""

# WEB TOOLS
SEARCH_DEFAULT_RESULTS = 5
SEARCH_MAX_RESULTS = 10

# Scraping Performance Tuning
SCRAPE_MAX_CHARS = 3000  # ✅ ACTIVE: Reduced from 10K for faster processing

# FILE TOOLS
LIST_DEFAULT_DEPTH = 2  # ✅ ACTIVE: Default directory traversal depth
LIST_SHOW_HIDDEN = False
LIST_SHOW_DETAILS = True
LIST_DEFAULT_PATTERN = "*"

# Future Performance Features (commented until implemented)
# SCRAPE_TIMEOUT = 10         # HTTP request timeout (trafilatura doesn't support)
# SCRAPE_PREVIEW_CHARS = 500  # Quick content previews
# FILE_PREVIEW_LIMIT = 5000   # File content truncation
# SHELL_TIMEOUT = 30          # System command timeout
# PARALLEL_TOOL_LIMIT = 3     # Max concurrent tool execution
# RESEARCH_MODE_SCRAPES = 2   # Limit deep research scraping
