# Changelog

## [2.1.0] - 2025-01-18

### New Features

- **Web capabilities**: Search (ddgs) and scrape (trafilatura) tools
- **Multi-provider support**: OpenAI, Anthropic, Gemini 
- **Result types**: `Ok[T]` and `Err[E]` for functional error handling
- **Streaming**: Event-coordinated streaming interface
- **Multitenancy**: Runtime user_id memory

### Architecture

- Protocol-based provider system with proper domain coupling
- Tool → Core → Lib → Infrastructure dependency flow
- AgentResult with conversation tracking
- Security validation and input sanitization

```python
# Same interface, expanded capabilities  
agent = Agent(tools=[Search(), Scrape()])
result = await agent("Search for Python best practices and summarize")
```
---

## [2.0.0] - 2025-08-15

### Complete Architectural Rewrite

After 340 commits exploring complex state management, v2.0.0 shifts to stateless context-driven architecture.

**Core Discovery**: Context injection works better than state management for LLM reasoning.

### New Features

- **Pure function agents**: `await agent("query")` - no objects, no setup
- **Context injection**: Automatic assembly from system, conversation, knowledge, memory sources
- **Graceful degradation**: Failed context sources don't break reasoning
- **Optional persistence**: Async conversation saving, zero writes in reasoning path

### Architecture Changes

- **Stateless design**: Pure functions replace persistent objects
- **Read-only context**: Error-resilient information assembly  
- **File storage**: JSON files replace SQLite complexity
- **Minimal dependencies**: 20+ dependencies → 2 core dependencies
- **Massive simplification**: 5000+ LOC → 830 LOC, 100+ files → 23 files

### Breaking Changes

Complete rewrite - not compatible with v1.x. Removed state objects, persistence layers, provider abstractions, and unused CLI.

### Design Principles

1. **Context is all you need** - Natural language beats structured state
2. **Reads enable, writes constrain** - Zero writes during reasoning  
3. **Simple beats complex** - Functions over objects, files over databases
4. **Graceful degradation** - Partial context better than no context

*First agent framework designed for how LLMs actually work, not traditional software patterns.*