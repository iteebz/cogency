# Contributing

## Quick Start

```bash
git clone https://github.com/iteebz/cogency.git
cd cogency
poetry install
just ci
```

## Why This Code is Clean

**Beautiful code is minimal and reads like English. One clear way to do each thing.**

This codebase follows the Beauty Doctrine:
- Zero ceremony interfaces (`Agent("name")`)
- Self-documenting code that reads like intent
- No wrapper classes that add no value
- Progressive disclosure - simple things simple, complex things possible

The result? A 5-tool agent framework that just works.

## Standards

**Run `just ci` before every commit—it formats, lints, tests, and builds:**
- **Format**: `just format` (ruff)
- **Lint**: `just fix` (ruff with fixes)
- **Test**: `just test` (pytest, >90% coverage)
- **Build**: `just build` (poetry)

**Code Style:**
- Type hints for public APIs
- Docstrings for user-facing functions
- No single-line imports (`from x import a, b` not separate lines)
- No local imports (import at module level)
- No `print()` statements (use logging)

## Architecture

**triage → reason → act → respond**

The 4-step pipeline defines the core execution flow. Everything else is built around it:
- **Agent**: Zero ceremony entry point
- **Tools**: `@tool` decorator auto-registers capabilities  
- **Memory**: LLM synthesis without external dependencies
- **Runtime**: Dependency injection with clean boundaries

## Tools

Tools are the extension point. They must:

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        # Name and natural language description
        super().__init__("my_tool", "Clear description")
    
    async def run(self, arg: str) -> dict:
        # Single responsibility
        # Validate inputs
        # Handle errors gracefully
        return {"result": f"Processed: {arg}"}
```

- Single responsibility (do one thing well)
- Auto-register via `@tool` decorator
- Comprehensive error handling
- Thorough tests (unit + integration)

## Pull Requests

```bash
git checkout -b feature/clear-name
# Make changes, add tests
just ci  # Must pass
# Submit PR with clear description linking any issues
```

**What We Look For:**
- Follows existing patterns
- Maintains zero ceremony principle
- Comprehensive tests
- Clear documentation

## What We Accept

- **Core Pipeline**: Improvements to triage/reason/act/respond
- **Tools**: New capabilities via `@tool` decorator
- **Memory**: LLM synthesis enhancements  
- **Providers**: LLM/embedding integrations
- **Docs**: Clear examples and API references

**What We Reject:**
- Wrapper classes without clear value
- Breaking the zero ceremony interface
- External dependencies without strong justification
- Complex abstractions where simple solutions exist

## Debugging

The codebase is designed for easy debugging:
- `debug=True` shows execution traces
- Clean error messages with context
- Minimal abstraction layers
- Self-contained components

When debugging production issues:
1. Strip abstractions → access raw data
2. Fix root cause → not symptoms  
3. Restore boundaries → re-add abstractions cleanly

## Testing

```bash
just test        # Run all tests
just test-cov    # With coverage
just eval-fast   # Run agent evaluations
```

- Mock external services
- Test error conditions
- Agent integration tests via evals
- Maintain >90% coverage (PRs with <90% must include justification)

## Documentation

- **User docs**: Clear examples that work
- **API docs**: Complete parameter descriptions
- **Examples**: Real-world usage patterns
- **Source code is the source of truth**: Keep documentation minimal

## Philosophy

**Zero ceremony. Adaptive intelligence. Production ready.**

We optimize for:
1. Developer productivity (simple interfaces)
2. Code clarity (reads like English)
3. Maintainability (minimal abstractions)
4. Extensibility (clean extension points)

The result is a codebase that's easy to understand, modify, and extend while remaining powerful enough for production use.

---

*Questions? Check `docs/` or open a GitHub discussion.*