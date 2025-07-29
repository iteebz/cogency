"""Comprehensive validation runner for cogency v1.0.0 production readiness."""

import asyncio
import sys
from pathlib import Path

# Add validation path to sys.path for imports
validation_path = Path(__file__).parent
sys.path.insert(0, str(validation_path))

# Production decorator validations
from decorators.robust_recovery import main as robust_main
from decorators.robust_checkpoints import main as checkpoint_main
from decorators.observe_metrics import main as observe_main
from decorators.rate_limiting import main as rate_limiting_main
from decorators.circuit_breaker import main as circuit_breaker_main

# Core feature validations
from memory.semantic_search import main as memory_main
from state.persistence import main as state_main
from modes.execution_modes import main as modes_main
from services.llm_providers import main as llm_main
from personality.identity_schema import main as personality_main
from tools.comprehensive_tools import main as tools_main

# Existing validations
from workflows.data_flow import main as workflow_main
from tracing.with_trace import main as tracing_main
from errors.recovery_tests import main as errors_main


async def run_validation_suite():
    """Run comprehensive cogency v1.0.0 validation suite."""
    print("🎯 COGENCY v1.0.0 COMPREHENSIVE VALIDATION SUITE")
    print("=" * 70)
    print("Testing production readiness across all features...")
    print("Using real LLM calls for authentic validation\n")
    
    validation_suites = [
        # Production hardening (critical for v1.0.0)
        ("🛡️  @robust Recovery", robust_main),
        ("💾 @robust Checkpoints", checkpoint_main), 
        ("📊 @observe Metrics", observe_main),
        ("⚡ Rate Limiting", rate_limiting_main),
        ("🔌 Circuit Breaker", circuit_breaker_main),
        
        # Core cognitive features
        ("🧠 Memory & Embeddings", memory_main),
        ("👥 State Persistence", state_main),
        ("🎯 Execution Modes", modes_main),
        ("🤖 LLM Providers", llm_main),
        ("🎭 Personality & Schema", personality_main),
        
        # Tools and integrations
        ("🔧 Comprehensive Tools", tools_main),
        ("📈 Workflow Processing", workflow_main),
        ("🔍 Tracing System", tracing_main),
        ("⚠️  Error Recovery", errors_main)
    ]
    
    results = {}
    total_time = 0
    
    for name, validation_func in validation_suites:
        print(f"🔸 Starting {name} validation...")
        print("-" * 50)
        
        import time
        start_time = time.time()
        
        try:
            success = await validation_func()
            results[name] = success
            suite_time = time.time() - start_time
            total_time += suite_time
            
            status = "🟢 PASS" if success else "🔴 FAIL"
            print(f"   Result: {status} ({suite_time:.1f}s)")
            
        except Exception as e:
            print(f"💥 {name} validation crashed: {e}")
            results[name] = False
            suite_time = time.time() - start_time
            total_time += suite_time
            print(f"   Result: 🔴 CRASH ({suite_time:.1f}s)")
        
        print("\n" + "=" * 70 + "\n")
    
    # Final comprehensive results
    print("📊 COGENCY v1.0.0 VALIDATION RESULTS:")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    critical_failed = []
    
    for name, success in results.items():
        status = "🟢 PASS" if success else "🔴 FAIL"
        print(f"{name:30} {status}")
        
        if success:
            passed += 1
        elif any(critical in name for critical in ["@robust", "@observe", "Memory", "State", "Tools"]):
            critical_failed.append(name)
    
    print("-" * 70)
    print(f"OVERALL VALIDATION SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"TOTAL VALIDATION TIME: {total_time:.1f}s")
    
    # Production readiness assessment
    if passed == total:
        print("\n🎉 COGENCY v1.0.0 IS PRODUCTION READY!")
        print("✨ All validation suites passed with real LLM testing")
        print("🚀 Ready for production deployment and user workloads")
        print("💎 Production hardening features are bulletproof")
    elif len(critical_failed) == 0 and passed >= total * 0.85:
        print(f"\n⚡ COGENCY v1.0.0 IS MOSTLY PRODUCTION READY!")
        print(f"🎯 {passed}/{total} suites passed - acceptable for v1.0.0")
        print("🔧 Consider addressing failed validations post-release")
    else:
        print(f"\n⚠️  COGENCY v1.0.0 NEEDS ATTENTION BEFORE RELEASE")
        print(f"🔧 {total - passed} validation suite(s) failed")
        if critical_failed:
            print(f"❌ Critical failures in: {', '.join(critical_failed)}")
        print("🚨 Address failed validations before v1.0.0 release")
    
    return passed == total


async def main():
    """Main entry point for comprehensive validation."""
    try:
        success = await run_validation_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())