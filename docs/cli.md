# CLI

Zero ceremony command line interface.

## Installation

```bash
pip install cogency
export OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY, etc.
```

## Usage

### Interactive Mode
```bash
cogency
# or
cogency --interactive
```

### Single Commands  
```bash
cogency "What's 2+2?"
cogency "Build a FastAPI app"
cogency "Analyze the logs in /var/log/"
```

## Tools

Built-in tools auto-load:
- **Files** - Local filesystem operations
- **Shell** - System command execution  
- **Search** - Web search
- **Scrape** - Web content extraction
- **Recall** - Memory retrieval

### Document Retrieve
```bash
export COGENCY_RETRIEVAL_PATH="/path/to/embeddings"
cogency "Find documentation about authentication"
```

## Configuration

CLI uses default Agent settings:
- Memory enabled
- All 6 built-in tools  
- Auto-detects LLM provider

For advanced configuration, use the Python API.