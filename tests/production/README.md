# Production Testing Suite

Comprehensive production readiness tests for the Cogency framework.

## Test Files

### `test_stress.py` (formerly `production_stress_test.py`)
Brutal production stress testing including:
- Single agent performance benchmarks
- Concurrent load testing (5 agents, 15 queries)
- Memory leak detection over 20 iterations
- Error recovery under load
- Long-running session stability

### `test_hardened.py` (formerly `production_hardened_test.py`) 
Production hardening feature validation:
- Basic functionality with metrics collection
- Rate limiting behavior testing
- Metrics collection and reporting
- Error recovery mechanisms
- JSON metrics export

### `test_edge_cases.py` (formerly `production_edge_case_test.py`)
Brutal edge case testing:
- Empty queries, extremely long queries (5000+ chars)
- Special characters, unicode, null bytes
- Complex analysis queries
- Rapid fire testing
- Memory stress testing with multiple agents

## Running Tests

```bash
# Run all production tests
poetry run python -m pytest tests/production/ -v

# Run specific test
poetry run python tests/production/test_stress.py
poetry run python tests/production/test_hardened.py
poetry run python tests/production/test_edge_cases.py
```

## Expected Results

- **Performance**: <10s average response time, >0.1 queries/sec throughput
- **Memory**: <50MB growth over extended sessions
- **Resilience**: Graceful rate limiting and error recovery
- **Reliability**: 50%+ success rate under brutal edge cases

All tests validate the production readiness of Cogency's resilience features including rate limiting, circuit breakers, metrics collection, and error recovery.