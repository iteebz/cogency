# Tools

## Built-in Tools

| Category | Tools |
|----------|-------|
| `code` | `read`, `write`, `edit`, `ls`, `find`, `replace`, `shell` |
| `web` | `scrape`, `search` |
| `memory` | `recall` |

```python
from cogency import Agent, tools

agent = Agent(tools=tools.defaults)   # All tools (code + web + memory)
agent = Agent(tools=tools.code)       # Code tools only
agent = Agent(tools=tools.web)        # Web tools only
```

## Tool Reference

### `read(file, start=0, lines=None)`
Read file contents. Use `start`/`lines` for pagination on large files.

### `write(file, content, overwrite=False)`
Write content to file. Fails if exists unless `overwrite=True`.

### `edit(file, old, new)`
Replace exact text block in file.

### `ls(path=".", pattern=None)`
List files in tree view (depth 3). Optional `pattern` filters filenames.

### `find(pattern=None, content=None, path=".")`
Find files by name pattern or search contents. At least one of `pattern` or `content` required.

### `replace(pattern, old, new, exact=True)`
Find-and-replace across files matching glob pattern.

### `shell(command, cwd=None)`
Execute shell command (30s timeout). Optional `cwd` for working directory.

### `scrape(url)`
Scrape webpage text (3KB limit).

### `search(query)`
Web search (5 results).

### `recall(query)`
Search past conversations (fuzzy keyword match).

## Custom Tools

```python
from dataclasses import dataclass
from typing import Annotated
from cogency import ToolResult
from cogency.core.tool import tool
from cogency.core.protocols import ToolParam

@dataclass
class QueryParams:
    sql: Annotated[str, ToolParam(description="SQL query to execute")]
    timeout: Annotated[int, ToolParam(description="Query timeout", ge=1, le=300)] = 30

@tool("Execute SQL queries against the database")
async def query_db(params: QueryParams, **kwargs) -> ToolResult:
    try:
        result = db.execute(params.sql, timeout=params.timeout)
        return ToolResult(outcome="Query successful", content=result)
    except Exception as e:
        return ToolResult(outcome=f"Query failed: {e}", error=True)

agent = Agent(tools=[query_db])
```

## Schema Format

| Field | Description |
|-------|-------------|
| `type` | `"string"`, `"integer"`, `"float"`, `"boolean"` |
| `description` | Human-readable docs for LLM |
| `required` | Boolean (default: True) |
| `default` | Default value |
| `ge`, `le` | Numeric constraints (greater/less than or equal) |
| `min_length`, `max_length` | String length constraints |

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

## Security Errors

Path validation errors use distinct messages for different failure modes:

| Error | Cause |
|-------|-------|
| `Invalid path` | Absolute path when relative expected, or path resolution failed |
| `Path outside sandbox` | Resolved path escapes allowed directory |

Both indicate security boundary enforcement. The distinction helps debugging.

## Guarantees

**No collision detection.** If a file changes after `read()` but before `edit()`, the write silently overwrites. Collision detection belongs in application logic.
