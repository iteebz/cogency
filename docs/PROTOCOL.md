# Streaming Protocol

## Explicit Agent State Signaling

**Problem:** Frameworks guess when agents need tools  
**Solution:** Agents explicitly signal execution state

```
§think: I need to examine the code structure first
§call: {"name": "file_read", "args": {"file": "main.py"}}
§execute
[SYSTEM: Found syntax error on line 15]
§respond: Fixed the missing semicolon. Code runs correctly now.
§end
```

Agent controls timing. Parser handles execution.

## Delimiters

- `§think:` Internal reasoning scratchpad
- `§call:` Single tool call as JSON object
- `§execute` Pause signal for tool execution
- `§respond:` Communication with human
- `§end` Task completion signal

## Examples

**Simple response (no tools):**
```
§respond: Python is a programming language created by Guido van Rossum.
§end
```

**Single tool call:**
```
§think: I should check what files exist first.
§call: {"name": "file_list", "args": {"path": "."}}
§execute
[SYSTEM: Found 3 files: main.py, config.json, README.md]
§respond: I found 3 files: main.py, config.json, README.md
§end
```

**Multiple sequential tools:**
```
§call: {"name": "file_list", "args": {"path": "."}}
§execute
[SYSTEM: Found: main.py, config.json]
§call: {"name": "file_read", "args": {"file": "config.json"}}
§execute
[SYSTEM: {"debug": false, "timeout": 30}]
§respond: This is a Node.js project with Express configuration.
§end
```

## Parser Events

Protocol generates structured events:

```python
{"type": "think", "content": "reasoning text", "timestamp": 1234567890.0}
{"type": "call", "content": "{\"name\": \"file_read\", \"args\": {\"file\": \"main.py\"}}", "timestamp": 1234567890.0}
{"type": "execute", "content": "", "timestamp": 1234567890.0}
{"type": "respond", "content": "final response", "timestamp": 1234567890.0}
{"type": "end", "content": "", "timestamp": 1234567890.0}
```

The canonical schema lives in `src/cogency/core/protocols.py` as the `Event` TypedDict. All parser, accumulator, and
bus consumers import that definition so changes propagate from a single source.

## Rules

1. **Tool calls must be valid JSON object:** `{"name": "file_read", "args": {"file": "example.py"}}`
2. **execute required after call:** Parser waits for tool execution
3. **Invalid JSON treated as content:** Parser continues with malformed calls as regular content
4. **end terminates stream:** Final event, no further processing
