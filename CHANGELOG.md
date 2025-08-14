# Changelog

## [2.0.0] - 2024-12-19

### 🚀 Complete Architectural Rewrite

After 340 commits exploring complex state management approaches, v2.0.0 represents a fundamental shift to stateless context-driven architecture.

### ✨ New Features

- **Pure Function Agents**: Agents are now simple functions - `await agent("query")`
- **Context Injection**: Automatic assembly of relevant context from multiple sources
- **Graceful Degradation**: Failed context sources don't break reasoning
- **Fire-and-Forget Persistence**: Optional async conversation saving
- **Minimal Dependencies**: Reduced from 20+ to 2 core dependencies

### 🏗️ Architecture Changes

- **Stateless Design**: No database writes during reasoning
- **Context Sources**: System, conversation, knowledge, memory, working context
- **Pure Functions**: All context assembly uses pure functions
- **File Storage**: Simple JSON file persistence instead of SQLite
- **Read-Only**: Context sources are read-only with error resilience

### 💥 Breaking Changes

- Complete API rewrite - not compatible with v1.x
- Removed complex state objects (Conversation, Workspace, Execution)
- Removed elaborate persistence layers and ACID requirements
- Removed provider abstraction and configuration complexity
- CLI removed (was unused)

### 🔧 Technical Details

- **Lines of Code**: Reduced from ~5000+ to ~830 lines
- **File Count**: Reduced from 100+ to 23 Python files
- **Dependencies**: Reduced from 20+ to 2 core dependencies
- **Performance**: Zero writes during reasoning vs multiple DB operations
- **Memory**: Pure functions vs persistent objects

### 🧪 Testing

- Added comprehensive test suite
- All tests pass without external dependencies (except LLM calls)
- Graceful degradation tested

### 📚 Documentation

- Complete README rewrite with working examples
- Technical blueprint in `docs/blueprint.md`
- Clear API reference and usage patterns

### 🎯 Design Principles

This rewrite follows strict principles discovered through empirical testing:

1. **Context is all you need** - LLMs work best with natural language context
2. **Reads enable, writes constrain** - Eliminate writes from reasoning path
3. **Simple beats complex** - Functions over objects, files over databases
4. **Graceful degradation** - Failed context sources don't break agents
5. **Optional persistence** - Learning and memory are enhancements, not requirements

### 🔬 Research Foundation

This architecture is backed by extensive exploration documented in 340 commits:
- Complex state management approaches tested and found inadequate
- Database-is-state patterns create more problems than they solve
- LLMs perform better with context injection than structured state
- Simpler architectures have better performance and fewer bugs

### 📈 Performance Impact

- **Latency**: Eliminated database writes from hot path
- **Throughput**: Pure functions vs complex object lifecycles
- **Memory**: No persistent state, automatic garbage collection
- **Reliability**: Graceful degradation vs complex error recovery

*This represents the first agent framework designed specifically for how LLMs actually work rather than how traditional software architectures work.*