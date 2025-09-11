# Streaming Protocol

## Explicit Agent State Signaling

**Problem:** Frameworks guess when agents need tools  
**Solution:** Agents explicitly signal execution state

```
§THINK: I need to examine the code structure first
§CALLS: [{"name": "read", "args": {"file": "main.py"}}]
§EXECUTE:
[SYSTEM: Found syntax error on line 15]
§RESPOND: Fixed the missing semicolon. Code runs correctly now.
§END:
```

Agent controls timing. Parser handles execution.

## Delimiters

- `§THINK:` Internal reasoning scratchpad
- `§CALLS:` Tool calls as JSON array
- `§EXECUTE:` Pause signal for tool execution
- `§RESPOND:` Communication with human
- `§END:` Task completion signal

## Examples

**Simple response (no tools):**
```
§RESPOND: Python is a programming language created by Guido van Rossum.
§END:
```

**Single tool call:**
```
§THINK: I should check what files exist first.
§CALLS: [{"name": "list", "args": {}}]
§EXECUTE:
[SYSTEM: Found 3 files: main.py, config.json, README.md]
§RESPOND: I found 3 files: main.py, config.json, README.md
§END:
```

**Multiple sequential tools:**
```
§CALLS: [{"name": "list", "args": {}}]
§EXECUTE:
[SYSTEM: Found: main.py, config.json]
§CALLS: [{"name": "read", "args": {"file": "config.json"}}]
§EXECUTE:
[SYSTEM: {"debug": false, "timeout": 30}]
§RESPOND: This is a Node.js project with Express configuration.
§END:
```

## Parser Events

Protocol generates structured events:

```python
{"type": "think", "content": "reasoning text", "timestamp": 1234567890.0}
{"type": "calls", "content": "[{...}]", "calls": [...], "timestamp": 1234567890.0}
{"type": "execute", "content": "", "timestamp": 1234567890.0}
{"type": "respond", "content": "final response", "timestamp": 1234567890.0}
{"type": "end", "content": "", "timestamp": 1234567890.0}
```

## Rules

1. **Tool calls must be valid JSON array:** `[{"name": "tool_name", "args": {...}}]`
2. **EXECUTE required after CALLS:** Parser waits for tool execution
3. **Invalid JSON triggers error event:** Parser emits error, continues
4. **END terminates stream:** Final event, no further processing