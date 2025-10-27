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

To create custom tools, subclass `cogency.Tool` and implement the `execute` method.

```python
from cogency import Tool, ToolResult

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"

    async def execute(self, sql: str, user_id: str):
        # Your implementation
        return ToolResult(
            outcome="Query executed",
            content="Results..."
        )

agent = Agent(llm="openai", tools=[DatabaseTool()])
```
