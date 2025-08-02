# Cogency Examples

Clean, focused examples showcasing core AI agent capabilities.

## 🚀 Core Examples

### `memory.py` - Persistent Memory
```bash
python memory.py
```
Save and recall information across conversations.

### `chat.py` - Interactive Chat
```bash
python chat.py
```
Interactive chat with memory and streaming responses.

### `coding.py` - Code Generation
```bash
python coding.py
```
ML engineering agent with shell and file tools for complex coding tasks.

### `research.py` - Deep Research
```bash
python research.py
```
Deep research agent with web scraping and search capabilities.

## Tool Coverage

Examples demonstrate 4 of 5 canonical tools:
- **Shell & Files**: `coding.py` uses shell commands and file operations
- **Scrape & Search**: `research.py` uses web scraping and search
- **HTTP**: Not covered (use directly: `Agent(tools=["http"])`)

## Getting Started

1. Start with `memory.py` for basic memory functionality
2. Try `chat.py` for interactive experience
3. Run `coding.py` to see tool usage in action
4. Use `research.py` for deep research workflows

No configuration needed - examples auto-detect your LLM provider from environment variables.