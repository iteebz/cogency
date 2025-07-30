# Cogency Validation

Comprehensive validation of Cogency's core functionality using real Agent runtime with standardized notify/trace output.

## Structure

**`framework.py`** - Common validation abstractions
- `BaseValidator` - Standard test execution with Agent runtime
- `ToolValidator` - Specialized for tool testing  
- `WorkflowValidator` - Multi-step workflow validation

**`human.py`** - Execute complete validation suite (human only)

## Categories

**`tools/`** - Core tool functionality
- Individual tool execution and correctness
- Fast feedback on basic operations

**`workflows/`** - Multi-step scenarios  
- Complex agent workflows
- Phase transitions and state flow
- Real-world usage patterns

**`memory/`** - Memory and persistence
- Semantic search validation
- State persistence across sessions
- Backend compatibility

**`notifications/`** - Output and tracing
- Trace output validation
- Silent vs verbose modes
- Notification system testing

**`errors/`** - Error handling
- Tool failure scenarios  
- Graceful degradation
- Recovery mechanisms

## Usage

```bash
# Run complete validation suite
poetry run python validation/run_all.py

# Individual test
poetry run python validation/tools/calculator.py

# Framework-based test
poetry run python validation/workflows/math.py
```

## Standards

All validation tests use:
- Real Cogency Agent runtime
- Standardized notify/trace output (EmojiFormatter)
- Consistent timeout and error handling
- Pattern validation for results
- Clean, minimal output (✓/✗ for results)

Framework ensures efficient, standardized validation across all test categories.