# Streaming Consciousness Test Suite

Comprehensive testing for the ceremony-eliminated streaming consciousness architecture.

## Test Categories

### 🔧 Core Tests (`test_stream_core.py`)
- Pure `stream()` function validation
- Configuration validation (required/optional parameters)
- Error propagation through recursive calls
- Tool normalization and default handling

### 🔒 Safety Tests (`test_loop_prevention.py`) - **HIGHEST PRIORITY**
- Recursion depth limits prevent infinite loops
- Circular tool dependency detection
- Malformed XML handling without parsing loops  
- Concurrent recursion safety

### 📝 XML Parsing (`test_xml_parsing.py`)
- XML boundary detection reliability
- Malformed XML resilience
- Edge cases (empty sections, special characters)
- Complex JSON parsing within tools sections

### ⚙️ Configuration (`test_config_surface.py`)
- Minimal configuration interface validation
- Default value behavior
- Configuration isolation between calls
- Edge cases and invalid input handling

### 🔗 Integration (`test_recursive_integration.py`)
- Multi-step tool execution workflows
- Error recovery patterns
- Dependent tool chains
- Concurrent workflow execution

### 📊 Stability (`test_stability_benchmarks.py`)
- Performance benchmarks and throughput
- Memory efficiency after ceremony elimination
- Stability under concurrent load
- Error recovery reliability

## Running Tests

### Quick Test Run
```bash
python run_tests.py
```

### Individual Test Categories
```bash
# Core functionality
python -m pytest tests/test_stream_core.py -v

# Safety (most critical)
python -m pytest tests/test_loop_prevention.py -v

# XML parsing
python -m pytest tests/test_xml_parsing.py -v

# Configuration
python -m pytest tests/test_config_surface.py -v

# Integration  
python -m pytest tests/test_recursive_integration.py -v

# Stability benchmarks
python -m pytest tests/test_stability_benchmarks.py -v -s
```

### All Tests
```bash
python -m pytest tests/ -v
```

## Test Architecture

### Mock Objects
- **MockLLM**: Configurable LLM responses for different scenarios
- **MockTools**: File operations, Python execution, etc.
- **BenchmarkLLM/Tools**: Performance-optimized mocks for benchmarking

### Key Testing Patterns
- **Recursion Safety**: Validate max_depth limits prevent infinite loops
- **Error Propagation**: Ensure failures bubble up correctly
- **Concurrent Execution**: Test thread safety and isolation
- **Memory Efficiency**: Validate ceremony elimination reduced footprint
- **Configuration Validation**: Test minimal config surface robustness

## Critical Safety Validations

1. **Loop Prevention**: `max_depth` limits enforced in all scenarios
2. **Error Handling**: All failure modes handled gracefully
3. **Memory Stability**: No leaks or excessive growth
4. **Concurrent Safety**: No race conditions or shared state issues
5. **Configuration Robustness**: Invalid inputs handled gracefully

## Success Criteria

✅ **All tests must pass before production deployment**

- Zero infinite loops under any input
- Graceful error handling for all failure modes  
- Memory usage remains stable under load
- Concurrent execution maintains isolation
- Configuration surface remains minimal and robust

The ceremony elimination should **improve** stability by reducing stateful complexity, not compromise it.