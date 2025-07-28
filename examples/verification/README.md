# Cogency Verification Examples 🎵

Test suite to verify Cogency's clean phase-based architecture is "singing".

## Structure

### `basic/` - Single Tool Verification
- Individual tool execution tests
- Verify each tool works correctly in isolation
- Fast feedback on tool functionality

### `workflows/` - Multi-Tool Scenarios  
- Complex workflows using multiple tools
- Test phase transitions and state propagation
- Real-world usage patterns

### `tracing/` - Debug Output Comparison
- Compare execution with/without tracing
- Verify debugging capabilities
- Performance comparison

### `errors/` - Error Handling & Recovery
- Tool failure scenarios
- Graceful error handling
- Recovery mechanisms

## Running Examples

```bash
# Single tool test
python examples/verification/basic/calculator_test.py

# With tracing
python examples/verification/tracing/with_trace.py

# Complex workflow
python examples/verification/workflows/math_verify.py
```

## Expected Results

Each example should demonstrate:
- ✅ Clean phase execution (preprocess → reason → act → respond)
- ✅ Proper tool integration and results
- ✅ State propagation through pipeline
- ✅ Beautiful, readable output
- ✅ Error handling when appropriate

If all examples run successfully, **Cogency is singing her beautiful song** 🎵