# Cogency XML Protocol

Three-phase execution: THINK → EXECUTE → RESULTS. Sequential, ordered, validated.

---

## THINK (Lenient)

Internal reasoning. LLM generates, system ignores.

```xml
<think>[any text]</think>
```

Optional. Unvalidated. Free-form.

---

## EXECUTE (Strict)

Tool invocation batch. System validates and executes sequentially in order.

```xml
<execute>
  <[tool_name]>
    <[arg_name]>[value]</[arg_name]>
  </[tool_name]>
</execute>
```

**System validates:**
- Tool name exists
- Arg names match schema
- Arg values are valid

**System executes:**
- Tools run sequentially, one completes before next starts
- Failed tool doesn't block subsequent tools
- All tools execute regardless of errors

---

## RESULTS (Lenient)

Tool outcomes. System generates, LLM reads. JSON array format, order-preserved.

```xml
<results>
[
  {"tool": "name", "status": "success", "content": data},
  {"tool": "name", "status": "failure", "content": "error message"}
]
</results>
```

- Results array order matches execution order exactly
- Status: "success" or "failure"
- Content: tool output on success, error message on failure
- All results returned (none skipped)

---

## Execution Semantics

**Sequential by default:**
```xml
<execute>
  <write><file>a.txt</file><content>x</content></write>
  <read><file>a.txt</file></read>
</execute>
```
Write completes, then read executes. Order guaranteed.

**Duplicate tools (order-preserved):**
```xml
<execute>
  <read><file>a.txt</file></read>
  <read><file>b.txt</file></read>
  <read><file>c.txt</file></read>
</execute>

<results>
[
  {"tool": "read", "status": "success", "content": "a"},
  {"tool": "read", "status": "success", "content": "b"},
  {"tool": "read", "status": "success", "content": "c"}
]
</results>
```
LLM knows which result is which by position.

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
All tools execute. Failures don't block subsequent tools.

---

## Complete Example

```xml
<think>read config, update endpoint, verify</think>

<execute>
  <read><file>config.json</file></read>
</execute>

<results>
[{"tool": "read", "status": "success", "content": {"api": "old.com"}}]
</results>

<think>writing updated config and verifying in one batch</think>

<execute>
  <write><file>config.json</file><content>{"api": "new.com"}</content></write>
  <read><file>config.json</file></read>
</execute>

<results>
[
  {"tool": "write", "status": "success", "content": {"bytes": 22}},
  {"tool": "read", "status": "success", "content": {"api": "new.com"}}
]
</results>

Config updated and verified.
```

---

## Guarantees

- **Sequential execution** - No race conditions possible
- **Order preserved** - Results array order matches execution
- **Batch safe** - LLM can batch any tools; dependent ops work
- **Validated** - Invalid tools/args rejected before execution
- **Complete** - All tool results returned, no skipping

---

## Parsing Responsibility

System parses: `<execute>` blocks only (validate tools/args)
System ignores: `<think>` content
System generates: `<results>` content (never parses own output)
LLM reads: `<results>` JSON

---

This is canonical. Reference grade. Sufficient but not verbose.
