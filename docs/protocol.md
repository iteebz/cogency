# Protocol

## Overview

**Wire Protocol:** What the LLM outputs (XML markers + JSON)
**Event Stream:** What consumers receive (typed JSON events)

Parser transforms wire protocol to events. Framework injects synthetic events (user, result, metric, error, interrupt).

---

## Wire Protocol

Three-phase execution: **THINK** → **EXECUTE** → **RESULTS**

See [execution.md](execution.md) for the complete canonical specification with edge cases.

```xml
<think>reasoning about the problem</think>

<execute>
[{"name": "read", "args": {"file": "config.json"}}]
</execute>

<results>
[{"tool": "read", "status": "success", "content": "..."}]
</results>

The config shows the API endpoint is set to production.
```

### THINK (Optional)

Internal reasoning. System ignores content.

```xml
<think>reasoning about the problem, what steps to take</think>
```

### EXECUTE (Strict)

Tool invocation as JSON array inside XML markers.

```xml
<execute>
[
  {"name": "tool_name", "args": {"arg": "value"}},
  {"name": "tool_name", "args": {"arg": "value"}}
]
</execute>
```

**Format:**
- JSON array of `{"name": str, "args": dict}` objects
- Parallel execution, results in array order
- Fault-tolerant: failed tool doesn't block subsequent tools

**Why JSON in XML?** Content like `</execute>` inside args is JSON-escaped, no collision with markers.

### RESULTS (System-Generated)

Tool outcomes. System generates, LLM reads.

```xml
<results>
[
  {"tool": "name", "status": "success", "content": data},
  {"tool": "name", "status": "failure", "content": "error message"}
]
</results>
```

Results array order matches execution order by position.

See [execution.md](execution.md) for edge cases (HTML in args, closing tags, mixed quotes).

---

## Event Stream

Parser transforms wire protocol into typed events.

### Event Types

| Event | Source | Purpose | Persisted |
|-------|--------|---------|-----------|
| `user` | Framework | User message | ✓ |
| `think` | LLM | Internal reasoning | ✓ |
| `call` | LLM | Tool invocation | ✓ |
| `execute` | LLM | Execution boundary | ✗ |
| `result` | Framework | Tool outcome | ✓ |
| `respond` | LLM | User-facing response | ✓ |
| `end` | LLM | Completion signal | ✗ |
| `metric` | Framework | Observability | ✗ |
| `error` | Framework | Failures | ✗ |
| `interrupt` | Framework | Cancellation | ✗ |
| `cancelled` | Framework | User cancellation | ✓ |

### Event Schema

```python
{"type": "user", "content": "What's in main.py?", "timestamp": 1234567890.0}
{"type": "think", "content": "reasoning text", "timestamp": 1234567890.0}
{"type": "call", "content": '{"name": "read", "args": {"file": "main.py"}}', "timestamp": 1234567890.0}
{"type": "execute", "timestamp": 1234567890.0}
{"type": "result", "content": "[...]", "payload": {"tools_executed": 1, "success_count": 1, "failure_count": 0}, "timestamp": 1234567890.0}
{"type": "respond", "content": "final response", "timestamp": 1234567890.0}
{"type": "end", "timestamp": 1234567890.0}
{"type": "metric", "step": {"input": 50, "output": 30}, "total": {"input": 100, "output": 50}, "timestamp": 1234567890.0}
```

Canonical schema: `src/cogency/core/protocols.py`

### Streaming Modes

```python
# stream="token": Real-time chunks
{"type": "think", "content": "I need", "timestamp": 1.0}
{"type": "think", "content": " to analyze", "timestamp": 1.1}

# stream="event": Complete units
{"type": "think", "content": "I need to analyze this", "timestamp": 1.0}

# stream=None: Non-streaming via LLM.generate()
```

---

## Storage

Events stored without delimiters. XML markers synthesized during context assembly.

**Stored:**
```python
{"type": "think", "content": "analyzing data"}
{"type": "call", "content": '{"name": "tool", ...}'}
```

**Assembled for LLM:**
```python
{"role": "assistant", "content": "<think>analyzing data</think>\n\n<execute>[...]</execute>"}
{"role": "user", "content": "<results>[...]</results>"}
```

Tool results become user messages (API constraint for Realtime/Live APIs).
