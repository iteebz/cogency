# Tools

## Built-in Tools

| Category | Tools |
|----------|-------|
| `code` | `read`, `write`, `edit`, `list`, `find`, `replace`, `shell` |
| `web` | `scrape`, `search` |
| `memory` | `recall` |

```python
from cogency import Agent, tools

agent = Agent(tools=tools.category(["code", "web"]))  # By category
agent = Agent(tools=tools.name(["read", "write"]))    # By name
agent = Agent(tools=tools())                          # All tools
```

## Tool Reference

### `read(file: str) -> str`
Read file contents.

### `write(file: str, content: str) -> str`
Write content to file.

### `edit(file: str, old: str, new: str) -> str`
Replace exact text block in file.

### `list(path: str) -> list[str]`
List files and subdirectories.

### `find(pattern: str = None, content: str = None, path: str = ".") -> list[str]`
Find files by name pattern or search contents. At least one of `pattern` or `content` required.

### `replace(pattern: str, old: str, new: str, exact: bool = True) -> str`
Find-and-replace across files matching glob pattern.

### `shell(command: str) -> str`
Execute shell command.

### `scrape(url: str) -> str`
Scrape URL content.

### `search(query: str) -> str`
Web search.

### `recall(query: str) -> str`
Search past conversations.

## Custom Tools

```python
from cogency import Tool, ToolResult

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    schema = {
        "sql": {"type": "string", "description": "SQL query", "required": True},
        "timeout": {"type": "integer", "default": 30, "min": 1, "max": 300},
    }

    def describe(self, args: dict) -> str:
        return f"Querying: {args.get('sql', '')[:50]}..."

    async def execute(self, sql: str, timeout: int = 30, **kwargs) -> ToolResult:
        try:
            result = db.execute(sql, timeout=timeout)
            return ToolResult(outcome="Query successful", content=result)
        except Exception as e:
            return ToolResult(outcome=f"Query failed: {e}", error=True)

agent = Agent(tools=[DatabaseTool()])
```

## Schema Format

| Field | Description |
|-------|-------------|
| `type` | `"string"`, `"integer"`, `"float"`, `"boolean"` |
| `description` | Human-readable docs for LLM |
| `required` | Boolean (default: True) |
| `default` | Default value |
| `min`, `max` | Numeric constraints |
| `max_length` | String length constraint |

## Error Handling

Tools should **not raise exceptions**. Return `ToolResult(error=True)`:

```python
async def execute(self, **kwargs) -> ToolResult:
    try:
        result = perform_operation()
        return ToolResult(outcome="Success", content=result)
    except Exception as e:
        return ToolResult(outcome=f"Failed: {e}", error=True)
```

Agent receives error as data and can reason about it.

## Guarantees

**No collision detection.** If a file changes after `read()` but before `edit()`, the write silently overwrites. Collision detection belongs in application logic.
