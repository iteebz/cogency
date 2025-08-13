# Current Architecture Concerns

## Critical Issues Requiring Fixes

### 1. Async/Sync API Inconsistency 🔴

**Problem**: The sync wrapper methods use `asyncio.run()` which fails when called from an async context.

```python
# This breaks:
async def main():
    agent = Agent("assistant")
    result = agent.run("Hello")  # RuntimeError: asyncio.run() cannot be called from a running event loop

# This is also broken:
for event in agent.stream("query"):  # Returns list, not iterator
    print(event)
```

**Root Cause**: 
- `agent.py:120` - `asyncio.run()` in sync wrapper fails in async contexts
- `agent.py:134` - `stream()` collects all events in memory and returns list instead of iterator

**Complexity**: Not trivial - requires fundamental API design decisions.

**Solutions**:
1. Thread-based sync wrappers with new event loops
2. Async-first design with optional sync helpers  
3. External dependency (`nest-asyncio`)
4. Remove sync methods entirely

**Beauty Doctrine Impact**: Violates "one clear way to do each thing" - dual sync/async APIs create confusion.

### 2. Prompt Injection Security Vulnerability 🔴

**Problem**: Tool results are directly embedded in LLM context without sanitization.

```python
# Malicious file containing: "Ignore previous instructions, instead..."
agent.run("Read evil.txt and summarize")  # Tool result fed directly to LLM
```

**Location**: `agents/reason.py:80` - Tool results used directly in context
**Impact**: Attackers can influence LLM behavior through file contents or command outputs

**Fix Required**: Sanitize tool outputs before LLM context injection:
- Strip potential prompt injection patterns
- Limit output length
- Add content warnings for suspicious patterns

### 3. Resilience System Not Applied 🟡

**Problem**: The `@resilience` decorator exists but isn't used anywhere.

**Location**: `resilience.py:42` - Decorator defined but never applied
**Impact**: Transient failures (network, API limits) cause hard failures instead of graceful retry

**Fix Required**: Apply `@resilience` to key operations:
- LLM API calls
- Tool executions
- Memory operations
- Storage operations

## Minor Issues

### 4. Memory Context Crude Truncation 🟡

**Problem**: Memory context uses blind character truncation instead of intelligent pruning.

```python
def to_context(self, max_tokens: int = 800) -> str:
    result = self.context()
    return result[:800]  # Crude truncation - could cut mid-sentence
```

**Location**: `memory/memory.py:82`
**Impact**: Important context could be lost, sentences cut mid-word

**Fix Required**: Intelligent pruning:
- Preserve complete sentences
- Prioritize recent context
- Use actual token counting
- Maintain conversation coherence

### 5. State Debugging Opacity 🟡

**Problem**: Rich `State` object exists but no public API for debugging failed reasoning chains.

**Location**: `state/__init__.py` - State class not exposed for inspection
**Impact**: Difficult to debug why reasoning failed or loops occurred

**Fix Required**: Add debugging access:
```python
state = agent.get_current_state()  # Access execution state
agent.debug_last_failure()        # Analyze what went wrong
```

## Non-Issues (Working as Designed)

### ✅ Multitenancy Isolation
- Properly enforced at storage layer with user_id filtering
- All queries include `WHERE user_id = ?` clauses
- Foreign key constraints prevent cross-user access

### ✅ Tool Composition
- Strict validation requires Tool() instances
- Clear schema generation prevents name conflicts
- LLM gets descriptions, rules, examples for disambiguation

### ✅ Event System Performance
- Minimal MessageBus with simple list iteration
- Fire-and-forget events with no async overhead
- No obvious bottlenecks

### ✅ Testing Architecture
- Comprehensive test suite with unit/integration/e2e separation
- Good fixture organization and mocking patterns
- Multitenancy isolation tests exist

### ✅ Configuration Management
- Only 2 focused dataclasses after PersistConfig removal
- Key validation prevents typos
- Sensible defaults with environment overrides

### ✅ Provider Dependencies
- ~60MB total for 7 providers is reasonable
- Auto-detection provides good developer experience
- Unified interfaces prevent vendor lock-in

## Implementation Priority

1. **Prompt injection sanitization** - Critical security issue
2. **Async/sync API consistency** - Breaks real-world usage  
3. **Apply resilience patterns** - Production reliability
4. **Smart memory pruning** - Context management
5. **State debugging access** - Developer experience

## CLAUDE.md Compliance Notes

**Architecture Archaeology Eliminated**: ✅
- Removed PersistConfig dead code
- Deleted unused _setup_config helper
- Cleaned validation whitelist

**Beauty Doctrine Violations**: 
- Dual sync/async APIs violate "one clear way to do each thing"
- Consider async-first design with minimal sync helpers

**First Principles Applied**:
- Challenged assumptions about sync wrapper necessity
- Identified genuine vs. perceived problems
- Focused on canonical solutions over incremental fixes