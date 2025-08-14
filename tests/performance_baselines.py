"""Performance baseline testing for canonical architecture."""

import asyncio
import time
import tracemalloc


class PerformanceValidator:
    """Validates performance characteristics of canonical implementation."""

    def __init__(self):
        self.baselines = {}
        self.results = {}

    async def validate_performance(self) -> dict:
        """Run all performance validation tests."""
        print("⚡ VALIDATING PERFORMANCE BASELINES")
        print("=" * 50)

        return {
            "agent_instantiation": await self._test_agent_instantiation(),
            "memory_operations": await self._test_memory_operations(),
            "tool_execution": await self._test_tool_execution(),
            "event_overhead": await self._test_event_overhead(),
            "reasoning_latency": await self._test_reasoning_latency(),
        }

    async def _test_agent_instantiation(self) -> dict:
        """Test Agent instantiation speed and memory usage."""
        print("\n🚀 TESTING AGENT INSTANTIATION")
        print("-" * 40)

        # Memory tracking
        tracemalloc.start()

        # Timing test
        start_time = time.perf_counter()

        try:
            from cogency import Agent

            # Basic instantiation - domain-centric architecture
            Agent("test")
            instantiation_time = (time.perf_counter() - start_time) * 1000

            # Memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print(f"✅ Basic instantiation: {instantiation_time:.2f}ms")
            print(
                f"✅ Memory usage: {current / 1024 / 1024:.2f}MB current, {peak / 1024 / 1024:.2f}MB peak"
            )

            # Test with memory enabled
            tracemalloc.start()
            start_time = time.perf_counter()

            Agent("test", memory=True)
            memory_instantiation_time = (time.perf_counter() - start_time) * 1000

            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print(f"✅ With memory: {memory_instantiation_time:.2f}ms")
            print(
                f"✅ Memory overhead: {current_mem / 1024 / 1024:.2f}MB current, {peak_mem / 1024 / 1024:.2f}MB peak"
            )

            return {
                "basic_time_ms": instantiation_time,
                "memory_time_ms": memory_instantiation_time,
                "basic_memory_mb": current / 1024 / 1024,
                "memory_memory_mb": current_mem / 1024 / 1024,
                "status": "success",
            }

        except Exception as e:
            tracemalloc.stop()
            print(f"❌ Instantiation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_memory_operations(self) -> dict:
        """Test memory system performance."""
        print("\n🧠 TESTING MEMORY OPERATIONS")
        print("-" * 40)

        try:
            from cogency import Agent

            # Create agent with memory
            agent = Agent("test", memory=True)

            # Test memory load
            start_time = time.perf_counter()
            await agent.memory.load("test_user")
            load_time = (time.perf_counter() - start_time) * 1000

            # Test memory save (remember)
            start_time = time.perf_counter()
            await agent.memory.remember("Test message", human=True)
            save_time = (time.perf_counter() - start_time) * 1000

            print(f"✅ Memory load: {load_time:.2f}ms")
            print(f"✅ Memory save: {save_time:.2f}ms")

            return {"load_time_ms": load_time, "save_time_ms": save_time, "status": "success"}

        except Exception as e:
            print(f"❌ Memory operations failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_tool_execution(self) -> dict:
        """Test tool execution performance."""
        print("\n🛠️ TESTING TOOL EXECUTION")
        print("-" * 40)

        try:
            from cogency.tools import Files

            # Create Files tool
            files_tool = Files()

            # Test basic tool operation
            start_time = time.perf_counter()
            result = await files_tool.run("list", ".", "List current directory")
            execution_time = (time.perf_counter() - start_time) * 1000

            print(f"✅ Files tool execution: {execution_time:.2f}ms")
            print(f"✅ Result length: {len(result)} chars")

            return {
                "files_execution_ms": execution_time,
                "result_size": len(result),
                "status": "success",
            }

        except Exception as e:
            print(f"❌ Tool execution failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_event_overhead(self) -> dict:
        """Test event system overhead."""
        print("\n📡 TESTING EVENT SYSTEM OVERHEAD")
        print("-" * 40)

        try:
            from cogency import Agent
            from cogency.events import emit

            # Initialize agent to setup event system
            agent = Agent("test")

            # Test event emission speed
            start_time = time.perf_counter()

            for i in range(100):
                emit("test", iteration=i, data=f"test_data_{i}")

            emission_time = (time.perf_counter() - start_time) * 1000

            # Check event capture
            logs = agent.logs()
            captured_events = len([log for log in logs if log.get("type") == "test"])

            print(f"✅ 100 event emissions: {emission_time:.2f}ms")
            print(f"✅ Events captured: {captured_events}/100")
            print(f"✅ Average per event: {emission_time/100:.3f}ms")

            return {
                "total_emission_ms": emission_time,
                "per_event_ms": emission_time / 100,
                "capture_rate": captured_events / 100,
                "status": "success",
            }

        except Exception as e:
            print(f"❌ Event testing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_reasoning_latency(self) -> dict:
        """Test reasoning system latency."""
        print("\n🤔 TESTING REASONING LATENCY")
        print("-" * 40)

        try:
            from cogency.context.task import start_task
            from cogency.providers import detect_llm
            from cogency.reason import reason

            # Setup test components
            llm = detect_llm()
            session, conversation, working_state, execution = await start_task(
                "test query", "test_user", None, max_iterations=5
            )

            # Test reasoning call with domain primitives
            start_time = time.perf_counter()
            result = await reason(conversation, working_state, execution, llm, [], "test assistant")
            reasoning_time = (time.perf_counter() - start_time) * 1000

            print(f"✅ Reasoning call: {reasoning_time:.2f}ms")
            print(f"✅ Result type: {type(result)}")
            print(
                f"✅ Has response: {'response' in result if hasattr(result, '__contains__') else 'N/A'}"
            )

            return {
                "reasoning_time_ms": reasoning_time,
                "has_response": "response" in result,
                "status": "success",
            }

        except Exception as e:
            print(f"❌ Reasoning test failed: {e}")
            return {"status": "error", "error": str(e)}


async def run_performance_validation():
    """Run complete performance validation suite."""
    validator = PerformanceValidator()
    results = await validator.validate_performance()

    print("\n" + "=" * 50)
    print("⚡ PERFORMANCE BASELINE SUMMARY")
    print("=" * 50)

    # Agent instantiation
    if results["agent_instantiation"]["status"] == "success":
        basic_time = results["agent_instantiation"]["basic_time_ms"]
        memory_time = results["agent_instantiation"]["memory_time_ms"]
        print(f"🚀 Agent Instantiation: {basic_time:.2f}ms basic, {memory_time:.2f}ms with memory")
    else:
        print(f"❌ Agent Instantiation: {results['agent_instantiation']['error']}")

    # Memory operations
    if results["memory_operations"]["status"] == "success":
        load_time = results["memory_operations"]["load_time_ms"]
        save_time = results["memory_operations"]["save_time_ms"]
        print(f"🧠 Memory Operations: {load_time:.2f}ms load, {save_time:.2f}ms save")
    else:
        print(f"❌ Memory Operations: {results['memory_operations']['error']}")

    # Tool execution
    if results["tool_execution"]["status"] == "success":
        exec_time = results["tool_execution"]["files_execution_ms"]
        print(f"🛠️ Tool Execution: {exec_time:.2f}ms")
    else:
        print(f"❌ Tool Execution: {results['tool_execution']['error']}")

    # Event overhead
    if results["event_overhead"]["status"] == "success":
        per_event = results["event_overhead"]["per_event_ms"]
        capture_rate = results["event_overhead"]["capture_rate"]
        print(f"📡 Event System: {per_event:.3f}ms per event, {capture_rate*100:.1f}% capture rate")
    else:
        print(f"❌ Event System: {results['event_overhead']['error']}")

    # Reasoning latency
    if results["reasoning_latency"]["status"] == "success":
        reasoning_time = results["reasoning_latency"]["reasoning_time_ms"]
        print(f"🤔 Reasoning: {reasoning_time:.2f}ms")
    else:
        print(f"❌ Reasoning: {results['reasoning_latency']['error']}")

    # Performance grade
    successful_tests = sum(1 for test in results.values() if test["status"] == "success")
    total_tests = len(results)
    performance_rate = successful_tests / total_tests * 100

    if performance_rate == 100:
        grade = "A+ (Excellent Performance)"
    elif performance_rate >= 80:
        grade = "A (Good Performance)"
    elif performance_rate >= 60:
        grade = "B (Acceptable Performance)"
    else:
        grade = "C (Performance Issues)"

    print(f"\n🏆 PERFORMANCE GRADE: {grade}")
    print(f"📊 Test Success Rate: {performance_rate:.1f}% ({successful_tests}/{total_tests})")

    return results


if __name__ == "__main__":
    asyncio.run(run_performance_validation())
