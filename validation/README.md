# Cogency Validation Suite 🎵

Comprehensive validation of Cogency's architecture and feature matrix.

## Structure

### `basic/` - Single Tool Verification
- Individual tool execution tests
- Tool isolation and correctness
- Fast feedback on core functionality

### `workflows/` - Multi-Tool Scenarios  
- Complex multi-step workflows
- Phase transitions and state propagation
- Real-world usage patterns

### `decorators/` - @robust & @observe Features
- Resilience, checkpointing, persistence validation
- Observability metrics collection
- Error recovery scenarios

### `backends/` - Memory & Persistence Systems
- Filesystem, Postgres, Chroma, Pinecone validation
- State persistence and checkpointing
- Backend switching and compatibility

### `modes/` - Fast vs Deep Mode
- Semantic summarization validation
- Mode switching behavior
- Context compression accuracy

### `tracing/` - Debug Output
- Trace output validation
- Silent vs verbose execution
- Performance impact measurement

### `errors/` - Error Handling & Recovery
- Tool failure scenarios  
- Graceful degradation
- Recovery mechanisms

## Running Validation

```bash
# Run all validation tests
python validation/run_all.py

# Single tool test
python validation/basic/calculator_test.py

# Complex workflow
python validation/workflows/math_verify.py
```

## Expected Results

Each example should demonstrate:
- ✅ Clean phase execution (preprocess → reason → act → respond)
- ✅ Proper tool integration and results
- ✅ State propagation through pipeline
- ✅ Beautiful, readable output
- ✅ Error handling when appropriate

If all examples run successfully, **Cogency is singing her beautiful song** 🎵