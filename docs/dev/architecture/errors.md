# Error Handling

Layered error handling with strategic Result pattern usage.

## Patterns by Layer

**Tools**: `Result.fail("message")` for operation failures
**Steps**: `None` for continue, exceptions for critical failures  
**Providers**: Exceptions wrapped in Results at boundaries
**Agent API**: String returns, ValueError for validation
**State**: Primitive types only, no Result objects

## Boundary Discipline

Results unwrapped at strategic points:

- Runtime: `llm_result.unwrap()`
- Response: `llm_result.unwrap()`
- State: Primitives only

Error observability via existing notification system (`debug=True`).
