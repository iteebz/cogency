# Streaming Protocol

## Two-Layer Architecture

**LLM Wire Protocol:** What the LLM outputs (delimited text stream)  
**Event Stream:** What the agent emits (structured JSON events)

Parser transforms wire protocol to events. Framework injects synthetic events (user, result, metric, error, interrupt).

---

## LLM Wire Protocol

**Problem:** Frameworks guess when agents need tools  
**Solution:** LLM explicitly signals execution state with XML markers and JSON payloads

See **[execution.md](execution.md)** for the canonical tool execution format.

The wire protocol uses three XML markers:
- `<think>...</think>` Internal reasoning scratchpad
- `<execute>[...]</execute>` Tool invocation batch (JSON array)
- `<results>[...]</results>` Tool execution outcomes (JSON array, system-generated)

The LLM generates thinking and execute blocks. The system generates results blocks. Parser transforms wire protocol to structured events.

### Examples

**Simple response (no tools):**
```xml
<respond>Python is a programming language created by Guido van Rossum.</respond>
```

**Single tool call:**
```xml
<think>I should check what files exist first.</think>

<execute>
[{"name": "list", "args": {"path": "."}}]
</execute>

<results>
[{"tool": "list", "status": "success", "content": ["main.py", "config.json", "README.md"]}]
</results>

I found 3 files: main.py, config.json, README.md
```

**Multiple sequential tools:**
```xml
<execute>
[
  {"name": "list", "args": {"path": "."}},
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>

<results>
[
  {"tool": "list", "status": "success", "content": ["main.py", "config.json", "README.md"]},
  {"tool": "read", "status": "success", "content": "{\"type\": \"module\", \"main\": \"index.js\"}"}
]
</results>

This is a Node.js project with Express configuration.
```

### Format Requirements

1. **Tool calls are JSON objects in array:** `[{"name": "read", "args": {...}}]`
2. **Arrays are wrapped in XML markers:** `<execute>[...]</execute>`
3. **Invalid JSON is an error:** Parser rejects and reports error
4. **All results returned:** No results are skipped regardless of success/failure

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
{"type": "call", "content": "{\"name\": \"read\", \"args\": {\"file\": \"main.py\"}}", "timestamp": 1234567890.0}
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
{"type": "call", "content": "{\"name\": \"read\", \"args\": {\"file\": \"main.py\"}}"}
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

---

## Filesystem Guarantees

Tools make **no collision detection** on file operations. If a file changes after `read()` but before `edit()`, the write silently overwrites the new content. This is by design—collision detection belongs in application logic (version control, explicit locking, optimistic retry patterns).

**Implication:** Agents should not assume atomicity across read→compute→write sequences. If concurrent file mutations are a concern, implement versioning at the application layer.

### Storage → Messages Transformation

Context assembly transforms stored events into proper conversational messages with wire protocol format:

**Input (events from storage):**
```python
[
  {"type": "user", "content": "debug app.py"},
  {"type": "think", "content": "should read file"},
  {"type": "call", "content": '{"name": "read", "args": {...}}'},
  {"type": "result", "content": '{"outcome": "Success", "content": "..."}'},
  {"type": "respond", "content": "fixed the bug"}
]
```

**Output (messages for LLM):**
```python
[
  {"role": "system", "content": "PROTOCOL + TOOLS"},
  {"role": "user", "content": "debug app.py"},
  {"role": "assistant", "content": "<think>should read file</think>\n\n<execute>\n[{\"name\": \"read\", \"args\": {...}}]\n</execute>"},
  {"role": "user", "content": "<results>\n[{\"tool\": \"read\", \"status\": \"success\", \"content\": \"...\"}]\n</results>"},
  {"role": "assistant", "content": "fixed the bug"}
]
```

**Key points:**
- XML markers and JSON arrays synthesized during assembly, not stored
- Events grouped by role (user vs assistant turns)
- Tool results become user messages (API constraint)
- Turn structure matches wire protocol (think → execute → results → respond)
- Chronological reconstruction collects granular call events, batches them in JSON array
