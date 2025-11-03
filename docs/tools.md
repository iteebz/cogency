# Built-in Tools

Cogency provides a set of built-in tools for agents, categorized for flexible inclusion in an agent's context.

## Tool Registration

Tools are registered and selected using the `tools` object, an instance of `ToolRegistry`. The `tools.category()` method allows you to select tools by category.

```python
from cogency import Agent, tools

# Include tools from the "code" and "web" categories
agent = Agent(tools=tools.category(["code", "web"]))

# Include only the "read" and "write" tools
agent = Agent(tools=tools.name(["read", "write"]))

# Include all tools
agent = Agent(tools=tools())  # Include all built-in tools
```

## Tool Categories

| Category | Description | Tools |
|---|---|---|
| `code` | Tools for interacting with the local filesystem. | `read`, `write`, `edit`, `list`, `find`, `replace`, `shell` |
| `web` | Tools for accessing web resources. | `scrape`, `search` |
| `memory` | Tools for recalling past interactions. | `recall` |

## Tool Reference

### `read(file: str) -> str`
Reads the content of a file.

### `write(file: str, content: str) -> str`
Writes content to a file.

### `edit(file: str, old: str, new: str) -> str`
Edits a file by replacing an exact block of text (`old`) with new content (`new`).

### `list(path: str) -> list[str]`
Lists the files and subdirectories within a specified path.

### `find(pattern: str) -> list[str]`
Finds files matching a glob pattern.

### `shell(command: str) -> str`
Executes a shell command and returns its output.

### `replace(pattern: str, old: str, new: str, exact: bool = True) -> str`
Performs find-and-replace operations across multiple files matching a glob pattern.

### `scrape(url: str) -> str`
Scrapes the content of a URL.

### `search(query: str) -> str`
Performs a web search and returns the results.

### `recall(query: str) -> str`
Recalls past interactions based on a query.

## Tool Extension

To create custom tools, subclass `cogency.Tool` and implement `execute()` and `describe()`.

### Minimal Tool

```python
from cogency import Tool, ToolResult

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    schema = {}

    def describe(self, args: dict) -> str:
        return f"Querying database: {args.get('sql', 'SQL query')}"

    async def execute(self, sql: str, **kwargs) -> ToolResult:
        try:
            result = db.execute(sql)
            return ToolResult(outcome="Query successful", content=result)
        except Exception as e:
            return ToolResult(outcome=f"Query failed: {e}", error=True)

agent = Agent(llm="openai", tools=[DatabaseTool()])
```

### Complete Tool with Schema

Document parameter types and constraints in `schema` dict.

```python
class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries on the database"
    schema = {
        "sql": {
            "type": "string",
            "description": "SQL SELECT query",
            "required": True,
            "max_length": 1000,
        },
        "timeout": {
            "type": "integer",
            "description": "Query timeout in seconds",
            "required": False,
            "default": 30,
            "min": 1,
            "max": 300,
        },
    }

    def describe(self, args: dict) -> str:
        sql = args.get("sql", "")[:50]  # Truncate for display
        return f"Executing query: {sql}..."

    async def execute(self, sql: str, timeout: int = 30, **kwargs) -> ToolResult:
        try:
            result = db.execute(sql, timeout=timeout)
            return ToolResult(outcome="Query executed successfully", content=result)
        except TimeoutError:
            return ToolResult(outcome="Query timeout exceeded", error=True)
        except Exception as e:
            return ToolResult(outcome=f"Query failed: {str(e)}", error=True)
```

### Schema Format

Each parameter can have:
- `type`: `"string"`, `"integer"`, `"float"`, `"boolean"`
- `description`: Human-readable docs for LLM
- `required`: Boolean (default: True)
- `default`: Default value
- `min`, `max`: Numeric constraints
- `max_length`: String length constraint

Schema is passed to LLM in system prompt via `tool_instructions()`. Helps LLM understand parameter semantics without documentation.

### Error Handling

Tools should **not raise exceptions**. Catch all errors and return `ToolResult(error=True)`:

```python
async def execute(self, **kwargs) -> ToolResult:
    try:
        result = perform_operation()
        return ToolResult(outcome="Success", content=result)
    except ValueError as e:
        return ToolResult(outcome=f"Invalid input: {e}", error=True)
    except Exception as e:
        return ToolResult(outcome=f"Execution failed: {e}", error=True)
```

This ensures the agent receives the error as data (via LLM) and can reason about it, rather than crashing the conversation.
