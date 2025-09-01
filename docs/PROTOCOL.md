# Streaming Protocol

## Explicit Agent State Signaling

**Problem:** Frameworks guess when agents need tools
**Solution:** Agents explicitly signal execution state

```python
§THINK: I need to examine the code structure first
§CALLS: [{"name": "file_read", "args": {"path": "main.py"}}]
§YIELD:
[SYSTEM: Found syntax error on line 15]
§RESPOND: Fixed the missing semicolon. Code runs correctly now.
```

LLM controls timing. Parser handles execution.

## Delimiters

- `§THINK:` Internal reasoning 
- `§CALLS:` Tool calls as JSON array
- `§YIELD:` Pause for tool execution
- `§RESPOND:` Final response

## Examples

**No tools needed:**
```
|||RESPOND: Python is a programming language created by Guido van Rossum.
```

**Single tool:**
```
|||THINK: I should check what files exist first.
|||TOOLS: [{"name": "file_list"}]
|||WAIT:
|||RESPOND: I found 3 files: main.py, config.json, README.md
```

**Multiple tools in sequence:**
```
|||TOOLS: [
  {"name": "file_list"},
  {"name": "file_read", "args": {"path": "config.json"}}
]
|||WAIT:
|||RESPOND: This is a Node.js project using Express and TypeScript.
```

## Parser Events

The protocol generates structured events:

```python
{"type": "think", "content": "reasoning text"}
{"type": "tools", "tools": [{"name": "file_read", "args": {...}}]}
{"type": "wait", "content": ""}  
{"type": "respond", "content": "final response"}
{"type": "end", "content": ""}
```

## Rules

1. Tools must be valid JSON array: `[{"name": "tool_name", "args": {...}}]`
2. Empty tools array means no execution: `|||TOOLS: []`
3. `|||WAIT:` required after non-empty tools
4. Invalid JSON triggers error event