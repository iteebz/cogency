# CLI Output Specification

## Symbol System

The CLI uses a minimal symbol system for clear, scannable interaction:

| Symbol | Purpose | Description |
|--------|---------|-------------|
| `>`    | User input | Messages from user to agent |
| `◦`    | Quick thinking | Decision for next actions |
| `*`    | Deep thinking | Self-reflection and complex reasoning |
| `•`    | Tool action | Tool execution in progress |
| `✓`    | Success | Successful tool completion |
| `✗`    | Failure | Failed tool completion |
| `→`    | Agent response | Final response to user |

## Formatting Rules

1. **Single newline** between all message types
2. **Tool pairs** are 2-line blocks (action + result) with no extra spacing between them
3. **No extra whitespace** or padding
4. **Consistent indentation** - no indentation for symbols

## Example Output

```
> Build me a web app

* Analyzing requirements and choosing architecture patterns

◦ Planning FastAPI application structure

• Create(app.py)
✓ File created (127 lines)

• Create(models.py)
✓ File created (45 lines)

◦ Setting up database and authentication

• Create(database.py)
✓ File created (89 lines)

• Shell(pip install fastapi uvicorn sqlalchemy)
✓ 8 packages installed

* Reviewing test failures and determining fix strategy

• Shell(pytest tests/)
✗ 2 tests failed - missing imports

• Update(app.py)
✓ Fixed import issues

• Shell(pytest tests/)
✓ All 12 tests passed

→ Complete FastAPI web application ready. Run with: uvicorn app:app --reload
```

## Implementation Notes

- Tool actions show: `Tool(specific_operation)`
- Results show brief, meaningful summaries
- Failures include actionable error context
- No verbose internal processing or debug info
- Clean, terminal-friendly ASCII symbols only