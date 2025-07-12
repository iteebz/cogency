# Changelog

## [0.3.0] - 2025-07-12

### 🚀 Revolutionary Streaming Architecture

**"You're not building a streamable agent. You're building an agent defined by its stream."**

#### Major Changes
- **Stream-First Design**: Complete architectural overhaul where every node is an async generator
- **Real-Time Transparency**: See agent thinking process as it happens, not reconstructed traces
- **Universal LLM Support**: Added OpenAI, Anthropic, Grok, and Mistral providers with streaming
- **Unified Interface**: Switch between any LLM provider with one line of code
- **Rate Limiting**: Built-in `yield_interval` parameter for all streaming functions

#### New Features
- `Agent.stream()` method for real-time execution streaming
- Streaming versions of all nodes: `plan_streaming()`, `reason_streaming()`, `act_streaming()`, `respond_streaming()`, `reflect_streaming()`
- Comprehensive streaming examples in `examples/`
- 47+ new streaming tests ensuring reliability
- Beautiful formatted output with thinking steps, chunks, results, and state updates

#### Breaking Changes
- Renamed `cogency.utils.cancellation` → `cogency.utils.interrupt` 
- All LLM providers now require `stream()` method implementation
- `@interruptable` decorator moved to `cogency.utils.interrupt`

#### LLM Providers Added
- **OpenAI**: GPT-4, GPT-3.5 with streaming support
- **Anthropic**: Claude 3 models with streaming
- **Grok**: X.AI's Grok with streaming  
- **Mistral**: All Mistral models with streaming
- **Enhanced Gemini**: Improved with better error handling

#### Developer Experience
- Stream chunks have consistent structure: `thinking`, `chunk`, `result`, `tool_call`, `error`, `state`
- Natural cancellation support via async generators
- No more black box agent execution - every step is visible
- Rate limiting ready for production usage

#### Documentation
- Updated README with streaming examples
- Comprehensive docstrings for all streaming functions
- Multiple example files demonstrating usage patterns

### Technical Details
- All streaming functions yield `Dict[str, Any]` chunks with standardized types
- Backward compatibility maintained for non-streaming `Agent.run()`
- LangGraph integration preserved while adding stream-native execution
- Robust error handling in streaming pipeline

This release fundamentally changes how AI agents work - making them truly transparent and observable in real-time.

---

## [0.2.x] - Previous Releases
See git history for previous release notes.