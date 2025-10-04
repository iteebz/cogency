# Streaming Protocol

## Two-Layer Architecture

**LLM Wire Protocol:** What the LLM outputs (delimited text stream)  
**Event Stream:** What the agent emits (structured JSON events)

Parser transforms wire protocol to events. Framework injects synthetic events (user, result, metric, error, interrupt).

---

## LLM Wire Protocol

**Problem:** Frameworks guess when agents need tools  
**Solution:** LLM explicitly signals execution state with delimiters

```
§think: I need to examine the code structure first
§call: {"name": "file_read", "args": {"file": "main.py"}}
§execute
§respond: Fixed the missing semicolon. Code runs correctly now.
§end
```

LLM controls timing. Parser detects delimiters and emits events. Accumulator handles execution.

### Delimiters

- `§think:` Internal reasoning scratchpad
- `§call:` Single tool call as JSON object
- `§execute` Pause signal for tool execution
- `§respond:` Communication with human
- `§end` Task completion signal

### Examples

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
§respond: I found 3 files: main.py, config.json, README.md
§end
```

**Multiple sequential tools:**
```
§call: {"name": "file_list", "args": {"path": "."}}
§execute
§call: {"name": "file_read", "args": {"file": "config.json"}}
§execute
§respond: This is a Node.js project with Express configuration.
§end
```

### Rules

1. **Tool calls must be valid JSON object:** `{"name": "file_read", "args": {"file": "example.py"}}`
2. **execute required after call:** Parser waits for tool execution
3. **Invalid JSON treated as content:** Parser continues with malformed calls as regular content
4. **end terminates stream:** Final event, no further processing

---

## Event Stream

Parser transforms LLM wire protocol into structured events. Framework injects additional events for complete conversation representation.

### Event Taxonomy

**Complete event types (10 total):**

| Event | Source | Purpose | Persisted |
|-------|--------|---------|-----------|
| `user` | Framework | User message | ✓ |
| `think` | LLM | Internal reasoning | ✓ |
| `call` | LLM | Tool invocation request | ✓ |
| `execute` | LLM | Tool execution boundary | ✗ |
| `result` | Framework | Tool execution outcome | ✓ |
| `respond` | LLM | User-facing response | ✓ |
| `end` | LLM | Task completion signal | ✗ |
| `metric` | Framework | Token/timing observability | ✗ |
| `error` | Framework | Execution failures | ✗ |
| `interrupt` | Framework | Cancellation (Ctrl+C, timeout) | ✗ |

**LLM-generated:** Parsed from wire protocol delimiters (§think:, §call:, §execute, §respond:, §end)  
**Framework-generated:** Synthetic events injected by agent runtime

### Event Schema

```python
# Conversation events
{"type": "user", "content": "What's in main.py?", "timestamp": 1234567890.0}
{"type": "think", "content": "reasoning text", "timestamp": 1234567890.0}
{"type": "call", "content": "{\"name\": \"file_read\", \"args\": {\"file\": \"main.py\"}}", "timestamp": 1234567890.0}
{"type": "execute", "timestamp": 1234567890.0}
{"type": "result", "payload": {"outcome": "Found file", "content": "...", "error": false}, "timestamp": 1234567890.0}
{"type": "respond", "content": "final response", "timestamp": 1234567890.0}
{"type": "end", "timestamp": 1234567890.0}

# Observability events
{"type": "metric", "step": {"input": 50, "output": 30, "duration": 0.8}, "total": {"input": 100, "output": 50, "duration": 1.5}, "timestamp": 1234567890.0}
{"type": "error", "payload": {"error": "Tool timeout after 30s", "tool": "shell"}, "timestamp": 1234567890.0}
{"type": "interrupt", "timestamp": 1234567890.0}
```

Canonical schema: `src/cogency/core/protocols.py` as `Event` TypedDict.

### Full Conversation Example

```python
async for event in agent("What's in main.py?"):
    print(event)
```

Output:
```python
{"type": "user", "content": "What's in main.py?"}
{"type": "think", "content": "I need to read the file"}
{"type": "call", "content": "{\"name\": \"file_read\", \"args\": {\"file\": \"main.py\"}}"}
{"type": "execute", "timestamp": 1234567890.0}
{"type": "result", "payload": {"outcome": "Read 50 lines", "content": "...", "error": false}}
{"type": "respond", "content": "The file contains a Flask app"}
{"type": "end", "timestamp": 1234567890.0}
{"type": "metric", "step": {"input": 60, "output": 40, "duration": 0.9}, "total": {"input": 120, "output": 80, "duration": 1.2}}
```

### Persistence

Only conversation events are persisted to storage:
- `user`, `think`, `call`, `result`, `respond`

Control flow (`execute`, `end`, `interrupt`) and observability (`metric`, `error`) are runtime-only.

**Storage format:** Events stored without delimiter syntax in content
```python
# Stored in database
{"type": "think", "content": "analyzing data"}  # Not "§think: analyzing data"
{"type": "call", "content": '{"name": "tool", ...}'}  # Not "§call: {...}"
```

---

## Architecture Flow

```
User Query
  ↓
Agent emits user event → [Event Stream]
  ↓
LLM streams wire protocol (§think:, §call:, ...)
  ↓
Parser transforms to events (think, call, ...)
  ↓
Accumulator executes tools → injects result events
  ↓
Metrics tracker → injects metrics events
  ↓
[Event Stream] → Display (renders all events)
              → Storage (persists conversation events only)

Next iteration
  ↓
Storage (load events)
  ↓
Context Assembly (to_messages)
  ↓
Messages (synthesized delimiters + proper roles)
  ↓
LLM receives conversational structure
```

Event stream is unified. Sources are diverse. Consumers see clean JSON events.

### Storage → Messages Transformation

Context assembly transforms stored events into proper conversational messages:

**Input (events from storage):**
```python
[
  {"type": "user", "content": "debug app.py"},
  {"type": "think", "content": "should read file"},
  {"type": "call", "content": '{"name": "file_read", ...}'},
  {"type": "result", "content": '{"outcome": "Success", ...}'},
  {"type": "respond", "content": "fixed the bug"}
]
```

**Output (messages for LLM):**
```python
[
  {"role": "system", "content": "PROTOCOL + TOOLS"},
  {"role": "user", "content": "debug app.py"},
  {"role": "assistant", "content": "§think: should read file\n§call: {...}\n§execute"},
  {"role": "user", "content": "§result: Success..."},
  {"role": "assistant", "content": "§respond: fixed the bug\n§end"}
]
```

**Key points:**
- Delimiters synthesized during assembly, not stored
- Events grouped by role (user vs assistant turns)
- `§execute` synthesized at call→result boundaries
- Tool results become user messages (API constraint)
- Turn structure matches LLM training distribution
