# Tool Execution Protocol

**Canonical specification for how the LLM invokes tools in Cogency.**

Single source of truth. Reference grade. Sufficient but not verbose.

---

## Overview

Three-phase execution: **THINK** → **EXECUTE** → **RESULTS**

The LLM generates thinking, optionally batches tool calls, system executes sequentially, returns results.

**Key constraint:** Tool invocations use JSON arrays inside XML markers to avoid content collisions.

---

## THINK (Optional, Lenient)

Internal reasoning scratch pad. System ignores content completely.

```xml
<think>reasoning about the problem, what steps to take</think>
```

- Optional: LLM may skip
- Unvalidated: Any content accepted
- Lenient: Format doesn't matter, not parsed
- Invisible: Not returned to user

---

## EXECUTE (Required for tools, Strict)

Tool invocation batch as JSON array.

```xml
<execute>
[
  {"name": "[tool_name]", "args": {"[arg_name]": "[value]"}},
  {"name": "[tool_name]", "args": {"[arg_name]": "[value]"}}
]
</execute>
```

### Format Rules

**JSON Array Structure:**
- Each element: `{"name": "tool_name", "args": {...}}`
- `name`: String, must be registered tool
- `args`: Object with schema-validated fields
- Order preserved: Execution order = array order

**Content Safety:**
- JSON string escaping handles any content safely
- No collision with XML delimiters
- Content like `</execute>` in args is JSON-escaped, safe

**System Validates:**
- JSON is valid (invalid JSON → error)
- Tool name exists (unknown tool → error)
- Arg names match schema (missing required args → error)
- Arg values are valid (wrong type → error)

**System Executes:**
- Sequential: One tool completes before next starts
- Ordered: Execution order matches array order
- Fault-tolerant: Failed tool doesn't block subsequent tools
- Complete: All tool results returned regardless of errors

### Single Tool

```xml
<execute>
[
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>
```

### Multiple Tools (Batched)

```xml
<execute>
[
  {"name": "read", "args": {"file": "a.txt"}},
  {"name": "write", "args": {"file": "b.txt", "content": "updated"}},
  {"name": "read", "args": {"file": "b.txt"}}
]
</execute>
```

All three execute sequentially. Read completes, write completes, read completes.

### Edge Cases Handled Safely

**HTML in args:**
```xml
<execute>
[
  {"name": "write", "args": {"file": "index.html", "content": "<html><body>Hello</body></html>"}}
]
</execute>
```
JSON escaping makes this safe (no XML collision).

**Closing tags in args:**
```xml
<execute>
[
  {"name": "write", "args": {"content": "Hello </write> world"}}
]
</execute>
```
The `</write>` is inside a JSON string. Parser sees it as content, not XML structure.

**Mixed quotes:**
```xml
<execute>
[
  {"name": "shell", "args": {"cmd": "echo \"hello\" && echo 'world'"}}
]
</execute>
```
JSON standard escaping handles all quotes.

---

## RESULTS (System-Generated, Lenient)

Tool execution outcomes. System generates JSON array, LLM reads.

```xml
<results>
[
  {"tool": "name", "status": "success", "content": data},
  {"tool": "name", "status": "failure", "content": "error message"}
]
</results>
```

### Format Rules

**JSON Array:**
- Each element: one tool result
- `tool`: String, tool name (matches execution order)
- `status`: `"success"` or `"failure"`
- `content`: On success = tool output (any JSON-serializable type), on failure = error message string
- Order: Results array order matches execution order exactly (by position)

**Guarantees:**
- Sequential order preserved
- All results returned (none skipped)
- Status indicates success/failure
- Content is the tool output or error

### Examples

**Success:**
```xml
<results>
[
  {"tool": "read", "status": "success", "content": "file contents"}
]
</results>
```

**Failure:**
```xml
<results>
[
  {"tool": "read", "status": "failure", "content": "File not found: config.json"}
]
</results>
```

**Batched results (order preserved):**
```xml
<results>
[
  {"tool": "read", "status": "success", "content": "a contents"},
  {"tool": "write", "status": "success", "content": {"bytes": 22}},
  {"tool": "read", "status": "success", "content": "b updated"}
]
</results>
```

LLM knows which result goes with which call by position. First call → first result.

**Mixed success/failure:**
```xml
<results>
[
  {"tool": "read", "status": "success", "content": "data"},
  {"tool": "write", "status": "failure", "content": "Permission denied"},
  {"tool": "read", "status": "success", "content": "data"}
]
</results>
```

Second tool failed, but first and third succeeded. LLM gets full picture.

---

## Complete Example

```xml
<think>Need to read config, update it, verify the change</think>

<execute>
[
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>

<results>
[
  {"tool": "read", "status": "success", "content": {"api": "old.com"}}
]
</results>

<think>API is old.com, need to update to new.com</think>

<execute>
[
  {"name": "write", "args": {"file": "config.json", "content": "{\"api\": \"new.com\"}"}},
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>

<results>
[
  {"tool": "write", "status": "success", "content": {"bytes": 22}},
  {"tool": "read", "status": "success", "content": {"api": "new.com"}}
]
</results>

Configuration updated successfully. API endpoint changed from old.com to new.com and verified.
```

---

## Design Principles

**Why JSON arrays in XML markers?**

1. **No collision:** Content like `</execute>` is JSON-escaped (inside a string), never seen as XML
2. **Simple for LLM:** Pure JSON, what models naturally generate
3. **Safe:** JSON libraries handle all escaping automatically
4. **Clear:** No special rules, standard JSON parsing works

**Why batch tools?**

1. **Efficiency:** Multiple tools in one call avoids round-trips
2. **Clarity:** Explicit which tools run together
3. **Optional:** LLM can use single-tool batches for safety if preferred

**Why sequential execution?**

1. **Deterministic:** Order guaranteed, no race conditions
2. **Simple:** Easier for LLM to reason about dependencies
3. **Safe:** Later tools can depend on earlier tools' results

---

## Implementation Details

**Parser:** `src/cogency/core/parser.py`
- Extracts JSON content from `<execute>` tags
- Validates JSON is array of objects with `name` and `args`
- Emits one call event per tool

**Accumulator:** `src/cogency/core/accumulator.py`
- Receives call events from parser
- Batches them until `execute` event arrives
- Executes sequentially using `execute_tools()`
- Formats results as JSON array

**Conversation:** `src/cogency/context/conversation.py`
- Stores granular call events (one per tool)
- Reconstructs by collecting calls, flushing on result
- Recreates JSON array format for protocol compliance

**System Prompt:** `src/cogency/context/system.py`
- Teaches LLM the JSON array format with examples
- Shows single and multi-tool batches
- Demonstrates success and failure handling

---

## Reference Implementation

All code examples above are tested and guaranteed to work. See test suite:
- Parser: `tests/unit/core/test_parser.py` (24 tests, all edge cases)
- Reconstruction: `tests/unit/context/test_conversation.py` (14 tests, roundtrip fidelity)
- Accumulator: `tests/unit/core/test_accumulator.py` (14 tests, execution flow)

---

## Canonical Status

This is the reference specification. All implementations use XML markers with JSON arrays.
