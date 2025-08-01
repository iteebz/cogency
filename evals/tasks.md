# Benchmark Tasks

Production-ready benchmarks for Cogency v1.0.0 release validation.

## Phase 1: Hardcoded MVP (Weekend)

### Core Benchmarks
- [ ] **SWE** - Software engineering tasks (3-5 hardcoded issues)
- [ ] **GAIA** - General assistant tasks (5-10 hardcoded questions) 
- [ ] **ToolPerformance** - Tool invocation latency (<100ms target)
- [ ] **LongHorizon** - Multi-step resilience (10-step with failure injection)

### Implementation
- [ ] Clean class names: `SWE`, `GAIA`, `ToolPerformance`, `LongHorizon`
- [ ] Hardcoded examples for rapid validation
- [ ] JSON result logging to `evals/results/`
- [ ] CI integration with exit codes

## Phase 2: Real Datasets (Following Week)

### Dataset Integration
- [ ] SWE-bench verified subset (20-50 real issues)
- [ ] GAIA Level 1-2 questions (50-100 real tasks)
- [ ] Reproducible benchmark runs for v1.0.0

## Success Criteria

**PASS Requirements:**
- SWE: ≥15% completion rate
- GAIA: ≥25% completion rate  
- ToolPerformance: <100ms average overhead
- LongHorizon: >80% completion with injected failures

**Current Status:** Framework ready, benchmarks needed

**Timeline:** Phase 1 complete by weekend, Phase 2 for v1.0.0 release