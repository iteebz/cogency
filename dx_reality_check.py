#!/usr/bin/env python3
"""
DX Reality Check: Fresh-eyes user testing for cogency framework
Tests the actual developer experience against marketing claims.
"""

import asyncio
import time
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DXMetric:
    """Represents a DX measurement."""
    name: str
    value: float
    unit: str
    expected: float
    status: str  # "pass", "fail", "warning"
    notes: str = ""

class DXTester:
    """Tests developer experience claims."""
    
    def __init__(self):
        self.metrics: List[DXMetric] = []
        self.test_results: Dict[str, Any] = {}
        self.temp_dir = None
        
    def record_metric(self, name: str, value: float, unit: str, expected: float, notes: str = ""):
        """Record a DX metric."""
        if value <= expected:
            status = "pass"
        elif value <= expected * 1.5:
            status = "warning"
        else:
            status = "fail"
            
        metric = DXMetric(name, value, unit, expected, status, notes)
        self.metrics.append(metric)
        return metric
    
    def test_installation_time(self) -> DXMetric:
        """Test how long it takes to install cogency."""
        print("🔧 Testing installation time...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        test_dir = Path(self.temp_dir) / "test_install"
        test_dir.mkdir()
        
        # Create a minimal pyproject.toml with absolute path
        project_root = Path(__file__).parent.resolve()
        pyproject_content = f'''[tool.poetry]
name = "cogency-test"
version = "0.1.0"
description = "Test installation"
authors = ["Test User <test@example.com>"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.12"
cogency = {{path = "{project_root}", develop = true}}

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''
        
        with open(test_dir / "pyproject.toml", "w") as f:
            f.write(pyproject_content)
        
        start_time = time.time()
        try:
            result = subprocess.run(
                ["poetry", "install"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            install_time = time.time() - start_time
            
            if result.returncode == 0:
                notes = "Installation successful"
            else:
                notes = f"Installation failed: {result.stderr}"
                install_time = 999  # Penalty for failure
                
        except subprocess.TimeoutExpired:
            install_time = 120
            notes = "Installation timed out"
        except Exception as e:
            install_time = 999
            notes = f"Installation error: {e}"
        
        return self.record_metric("installation_time", install_time, "seconds", 30, notes)
    
    def test_hello_world_time(self) -> DXMetric:
        """Test time to get hello world working."""
        print("👋 Testing hello world time...")
        
        if not self.temp_dir:
            return self.record_metric("hello_world_time", 999, "seconds", 10, "No test environment")
        
        test_dir = Path(self.temp_dir) / "test_install"
        hello_world_code = '''from cogency import Agent
import asyncio

async def main():
    agent = Agent("test")
    result = await agent.run("Hello world")
    print(f"Response: {result}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        hello_file = test_dir / "hello.py"
        with open(hello_file, "w") as f:
            f.write(hello_world_code)
        
        start_time = time.time()
        try:
            result = subprocess.run(
                ["poetry", "run", "python", "hello.py"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            hello_time = time.time() - start_time
            
            if result.returncode == 0 and "Response:" in result.stdout:
                notes = "Hello world successful"
            else:
                notes = f"Hello world failed: {result.stderr}"
                hello_time = 999
                
        except subprocess.TimeoutExpired:
            hello_time = 30
            notes = "Hello world timed out"
        except Exception as e:
            hello_time = 999
            notes = f"Hello world error: {e}"
        
        return self.record_metric("hello_world_time", hello_time, "seconds", 10, notes)
    
    def test_agent_creation_overhead(self) -> DXMetric:
        """Test overhead of creating an agent."""
        print("🤖 Testing agent creation overhead...")
        
        try:
            from cogency import Agent
            
            # Measure agent creation time
            start_time = time.time()
            agent = Agent("test")
            creation_time = time.time() - start_time
            
            notes = "Agent created successfully"
            
        except Exception as e:
            creation_time = 999
            notes = f"Agent creation failed: {e}"
        
        return self.record_metric("agent_creation_time", creation_time * 1000, "ms", 100, notes)
    
    def test_first_query_latency(self) -> DXMetric:
        """Test latency of first query (includes LLM initialization)."""
        print("🚀 Testing first query latency...")
        
        try:
            from cogency import Agent
            
            agent = Agent("test")
            
            start_time = time.time()
            result = asyncio.run(agent.run("What is 2+2?"))
            query_time = time.time() - start_time
            
            if result and "4" in result:
                notes = "First query successful"
            else:
                notes = f"First query returned unexpected result: {result}"
                query_time = 999
                
        except Exception as e:
            query_time = 999
            notes = f"First query failed: {e}"
        
        return self.record_metric("first_query_latency", query_time, "seconds", 3, notes)
    
    def test_import_complexity(self) -> DXMetric:
        """Test complexity of imports needed."""
        print("📦 Testing import complexity...")
        
        # Test the magical single import
        try:
            from cogency import Agent
            import_count = 1
            notes = "Single import successful"
        except Exception as e:
            import_count = 999
            notes = f"Single import failed: {e}"
        
        return self.record_metric("import_complexity", import_count, "imports", 1, notes)
    
    def test_memory_usage(self) -> DXMetric:
        """Test memory usage of basic agent."""
        print("🧠 Testing memory usage...")
        
        try:
            import psutil
            from cogency import Agent
            
            # Get baseline memory
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create agent
            agent = Agent("test")
            
            # Measure memory after agent creation
            after_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_overhead = after_memory - baseline_memory
            
            notes = f"Memory overhead: {memory_overhead:.1f} MB"
            
        except Exception as e:
            memory_overhead = 999
            notes = f"Memory test failed: {e}"
        
        return self.record_metric("memory_overhead", memory_overhead, "MB", 50, notes)
    
    def test_line_count_dx(self) -> DXMetric:
        """Test actual lines of code needed for basic usage."""
        print("📝 Testing line count for basic usage...")
        
        # Count lines in minimal working example
        minimal_code = '''from cogency import Agent
import asyncio

async def main():
    agent = Agent("assistant")
    result = await agent.run("Hello world")
    print(result)

asyncio.run(main())
'''
        
        lines = len([line for line in minimal_code.split('\n') if line.strip()])
        
        return self.record_metric("minimal_lines_of_code", lines, "lines", 6, "Lines for hello world")
    
    def test_startup_time(self) -> DXMetric:
        """Test cold startup time of the framework."""
        print("⏱️ Testing startup time...")
        
        startup_code = '''
import time
start = time.time()
from cogency import Agent
import_time = time.time() - start
print(f"Import time: {import_time:.3f}s")
'''
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", startup_code],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "Import time:" in result.stdout:
                import_time = float(result.stdout.split("Import time: ")[1].split("s")[0])
                notes = "Startup successful"
            else:
                import_time = 999
                notes = f"Startup failed: {result.stderr}"
                
        except Exception as e:
            import_time = 999
            notes = f"Startup error: {e}"
        
        return self.record_metric("startup_time", import_time, "seconds", 1, notes)
    
    def check_api_simplicity(self) -> Dict[str, Any]:
        """Check API simplicity claims."""
        print("🎯 Checking API simplicity...")
        
        checks = {
            "single_import": False,
            "no_config_needed": False,
            "async_by_default": False,
            "auto_llm_detection": False,
            "magical_dx": False
        }
        
        try:
            # Test single import
            from cogency import Agent
            checks["single_import"] = True
            
            # Test no config needed
            agent = Agent("test")
            checks["no_config_needed"] = True
            
            # Test async by default
            import inspect
            run_method = getattr(agent, 'run')
            checks["async_by_default"] = inspect.iscoroutinefunction(run_method)
            
            # Test auto LLM detection
            checks["auto_llm_detection"] = agent.llm is not None
            
            # Test magical DX (subjective)
            checks["magical_dx"] = all([
                checks["single_import"],
                checks["no_config_needed"], 
                checks["async_by_default"],
                checks["auto_llm_detection"]
            ])
            
        except Exception as e:
            print(f"API check failed: {e}")
        
        return checks
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all DX tests."""
        print("🧪 Running DX Reality Check...\n")
        
        # Core performance tests
        self.test_installation_time()
        self.test_hello_world_time()
        self.test_agent_creation_overhead()
        self.test_first_query_latency()
        self.test_startup_time()
        
        # DX quality tests
        self.test_import_complexity()
        self.test_line_count_dx()
        self.test_memory_usage()
        
        # API simplicity check
        api_checks = self.check_api_simplicity()
        
        # Clean up
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        
        return {
            "metrics": self.metrics,
            "api_checks": api_checks,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive DX report."""
        results = self.run_all_tests()
        
        report = ["", "🎯 COGENCY DX REALITY CHECK REPORT", "=" * 50, ""]
        
        # Performance metrics
        report.append("📊 PERFORMANCE METRICS:")
        report.append("-" * 30)
        
        for metric in self.metrics:
            status_emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌"}[metric.status]
            report.append(f"{status_emoji} {metric.name}: {metric.value:.2f} {metric.unit} (expected: ≤{metric.expected})")
            if metric.notes:
                report.append(f"   └─ {metric.notes}")
        
        # API checks
        report.append("\n🎯 API SIMPLICITY CHECKS:")
        report.append("-" * 30)
        
        for check, passed in results["api_checks"].items():
            status = "✅" if passed else "❌"
            report.append(f"{status} {check.replace('_', ' ').title()}")
        
        # Overall assessment
        report.append("\n🏆 OVERALL ASSESSMENT:")
        report.append("-" * 30)
        
        passed = sum(1 for m in self.metrics if m.status == "pass")
        warned = sum(1 for m in self.metrics if m.status == "warning")
        failed = sum(1 for m in self.metrics if m.status == "fail")
        
        report.append(f"✅ Passed: {passed}")
        report.append(f"⚠️ Warnings: {warned}")
        report.append(f"❌ Failed: {failed}")
        
        if failed == 0 and warned <= 1:
            report.append("\n🎉 DX VERDICT: WORLD-CLASS")
        elif failed <= 1:
            report.append("\n👍 DX VERDICT: GOOD")
        else:
            report.append("\n👎 DX VERDICT: NEEDS IMPROVEMENT")
        
        report.append(f"\n⏰ Generated: {results['timestamp']}")
        
        return "\n".join(report)

def main():
    """Run the DX reality check."""
    tester = DXTester()
    report = tester.generate_report()
    print(report)
    
    # Save report
    with open("dx_reality_check_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: dx_reality_check_report.txt")

if __name__ == "__main__":
    main()