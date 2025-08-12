# AGI Lab Standard Evaluation Suite

## Core Principle

**Measure quality, don't assert correctness.** Evals are continuous measurement, not binary pass/fail.

## Evaluation Types

### Internal Evals (`evals/internal/`)

- Quality regression detection
- Custom behavior measurement
- Development feedback loops

### Benchmarks (`evals/benchmarks/`)

- Public benchmark comparisons
- Industry standard metrics
- External validation

## Gold Standard Implementation

### 1. Multi-Model LLM Judges (Primary)

```python
# Use different model family than your agent
def evaluate_response(agent_output, criteria):
    judge_prompt = f"""
    Rate this agent response on {criteria} from 1-10.
    Consider: accuracy, completeness, clarity.
    
    Response: {agent_output}
    """
    return judge_llm.score(judge_prompt)
```

**Critical**: Never use a model to judge itself. If agent uses Gemini, judge with Claude/GPT.

### 2. Outcome-Based Measurement (When Possible)

```python
# Verify actual task completion
def check_task_success(environment, expected_outcome):
    return {
        'file_created': check_file_exists(path),
        'api_called': verify_api_logs(),
        'goal_achieved': measure_end_state()
    }
```

### 3. Human Validation (Sample)

- Rate 5-20 examples per week (not all outputs)
- Target: low confidence scores, detected regressions, 10% random sample
- Use to validate LLM judge reliability and catch systematic errors

### Human Review Triggers

```python
def queue_for_human_review(response, metadata):
    if (
        llm_judge_confidence < 0.7 or      # Judge uncertain
        score_changed_significantly or      # Regression detected  
        random.random() < 0.1              # 10% random sample
    ):
        save_for_human_review(response, metadata)
```

### 4. Raw Output Logging (Critical Infrastructure)

```python
eval_result = {
    'timestamp': now(),
    'test_case': test_name,
    'agent_response': full_response,
    'thinking_tokens': intermediate_steps,  # If available
    'tool_calls': api_calls_made,
    'llm_judge_score': judge_score,
    'llm_judge_reasoning': judge_explanation,
    'human_score': None,  # Filled later if reviewed
    'metadata': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.7,
        'context_length': 1500,
        'session_id': session_uuid
    }
}
```

**Critical**: Save everything. Enables meta-analysis, debugging, and retrospective evaluation improvements.

### 5. Structural Validation (Safety Net)

```python
# Basic sanity checks
def validate_structure(response):
    return {
        'valid_json': is_valid_json(response),
        'required_fields': has_required_fields(response),
        'reasonable_length': 50 < len(response) < 5000
    }
```

## Benchmark Strategy

### Recommended Public Benchmarks

1. **SWE-bench** (mini-bench: 100-300 examples from SWE-bench Lite)
- Tests coding + tool orchestration
- Perfect for agents with shell/file capabilities
2. **GAIA** (mini-bench: 50 examples per difficulty level)
- Multi-step reasoning with web search
- Tests information synthesis across tools

### Custom Memory Benchmark (Differentiator)

Design temporal evaluation that showcases persistent memory:

```python
# Example: Cross-session dependency
Day 1: "Research Project Alpha, store key findings"
Day 2: "Work on unrelated Project Beta" 
Day 3: "Continue Project Alpha using Day 1 findings"
      # Context cleared between sessions
```

**Hack-resistant design:**

- Force actual memory system usage (context clearing)
- Cross-session dependencies requiring specific details
- Memory interference (multiple overlapping projects)
- Temporal ordering tests (which facts from which session?)

**Key insight**: Well-designed custom benchmark > weak public benchmark

## Statistical Requirements

### Sample Sizes (Solo Developer)

- **50+ examples** per behavior for trends
- **100+ examples** for confident regression detection
- **20+ edge cases** for error handling

### Mini-Bench Approach

- Use subsets of large benchmarks (SWE-bench Lite, GAIA samples)
- Focus on methodology over completeness
- Can scale up later if needed

### Tracking Over Time

```python
# Focus on relative changes, not absolute scores
def track_performance():
    current_scores = run_eval_suite()
    regression_detected = current_scores < (baseline * 0.95)
    return regression_detected
```

## Evaluation Structure

### Recommended Categories

```
evals/internal/
  reasoning/              # Logic and problem-solving  
    test_math_problems.py     # 100+ examples
    test_logical_chains.py    # 100+ examples
  
  tool_usage/             # API calls and external tools
    test_correct_apis.py      # 100+ examples
    test_parameter_handling.py # 50+ examples
  
  error_handling/         # Graceful failures
    test_invalid_inputs.py    # 50+ edge cases
    test_timeout_recovery.py  # 30+ examples
  
  memory/                 # Cross-session capabilities
    test_temporal_recall.py   # Custom benchmark
    test_context_injection.py # User profile usage
  
  regression/             # Production failures
    test_known_failures.py    # Growing set
```

### Evaluation Runner

```python
def run_internal_evals():
    results = {}
    for category in ['reasoning', 'tool_usage', 'error_handling', 'memory']:
        scores = evaluate_category(category)
        results[category] = {
            'avg_score': np.mean(scores),
            'regression': scores < baseline[category],
            'sample_size': len(scores)
        }
    return results
```

## 80/20 Implementation (Solo Developer)

### Phase 1: Minimum Viable

1. **LLM judge with different model family** (Claude judging Gemini agent)
2. **SWE-bench + GAIA mini-benchmarks** (50-100 examples each)
3. **Basic custom memory benchmark** (cross-session tasks)
4. **Raw output logging with full metadata**
5. **Weekly human spot-check** on 10 examples (confidence-triggered)

### Phase 2: Enhanced

1. **Increase to 100+ examples** per category
2. **Add regression suite** from production failures
3. **Automated regression detection**
4. **Memory benchmark refinement** (temporal ordering, interference testing)

### Phase 3: Production-Ready

1. **300+ examples** for statistical confidence
2. **A/B testing framework**
3. **Human validation pipeline**
4. **Comprehensive benchmark coverage**

## Red Flags to Avoid

❌ **Self-judging models** (Gemini judging Gemini outputs)  
❌ **Tiny test sets** (<20 examples per behavior)  
❌ **Only string matching** (brittle for generative AI)  
❌ **No human validation** (LLM judges can be systematically wrong)  
❌ **Absolute scoring without baselines** (focus on relative performance)
❌ **Weak public benchmarks** (ToolBench, API-Bank) over well-designed custom ones

## Implementation Priority

1. **Start**: LLM judges + SWE-bench/GAIA mini + basic memory benchmark
2. **Scale**: More examples + human validation + raw logging
3. **Optimize**: Statistical rigor + temporal benchmark sophistication

Remember: Perfect measurement is impossible. Use multiple imperfect signals to detect quality regressions and guide development. Your memory capabilities are a key differentiator - showcase them thoughtfully.