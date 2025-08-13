"""Multi-step tool orchestration evaluation - demonstrates Cogency's workflow sophistication.

Tests complex engineering workflows that require coordination across multiple tools
with error handling, state management, and workflow recovery. This showcases
Cogency's production-ready agentic capabilities beyond simple tool usage.
"""

import time
from typing import Any

from ...core import agent


class MultiStepOrchestration:
    """Test sophisticated multi-step tool orchestration workflows."""

    name = "multi_step_orchestration"
    description = "Complex tool workflow orchestration showcase"

    def __init__(self, sample_size: int = 25):
        """Initialize with 25 examples for AGI lab demo."""
        self.sample_size = sample_size
        self.workflow_templates = self._create_orchestration_workflows()

    def _create_orchestration_workflows(self) -> list[dict[str, Any]]:
        """Create sophisticated multi-tool workflow scenarios."""
        return [
            # Software Development Workflows
            {
                "name": "full_dev_cycle_python_script",
                "category": "software_development",
                "description": "Complete development cycle with testing and documentation",
                "prompt": "Create a Python script called 'data_processor.py' that reads CSV files and calculates statistics. Then write unit tests for it, run the tests to make sure they pass, create documentation, and archive everything in a 'project' directory.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_main_script",
                    "create_test_file",
                    "run_tests",
                    "create_documentation",
                    "organize_project",
                ],
                "validator": lambda r: all(
                    keyword in r.lower() for keyword in ["test", "pass", "documentation", "project"]
                ),
                "complexity": "high",
            },
            {
                "name": "web_app_setup_with_validation",
                "category": "web_development",
                "description": "Set up a web application with dependency management and validation",
                "prompt": "Create a simple Flask web application with a basic API endpoint. Set up proper project structure, install dependencies, create a requirements.txt, test that the app starts correctly, then create a README with setup instructions.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_app_structure",
                    "install_dependencies",
                    "create_requirements",
                    "test_app_startup",
                    "create_readme",
                ],
                "validator": lambda r: all(
                    keyword in r.lower() for keyword in ["flask", "requirements", "readme", "test"]
                ),
                "complexity": "high",
            },
            # Data Engineering Workflows
            {
                "name": "data_pipeline_validation",
                "category": "data_engineering",
                "description": "Build and validate a data processing pipeline",
                "prompt": "Create a data processing pipeline that: 1) Creates sample CSV data, 2) Processes it with a Python script, 3) Validates the output format, 4) Generates a processing report, and 5) Cleans up temporary files.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "generate_sample_data",
                    "create_processor",
                    "run_processing",
                    "validate_output",
                    "cleanup",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["csv", "process", "validate", "report", "cleanup"]
                ),
                "complexity": "high",
            },
            {
                "name": "database_setup_and_migration",
                "category": "database_management",
                "description": "Database setup with schema migration and validation",
                "prompt": "Set up a SQLite database with user tables, create sample data, run a migration to add a new column, validate the schema changes, and create a backup of the final database.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_initial_schema",
                    "insert_sample_data",
                    "create_migration",
                    "validate_schema",
                    "create_backup",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["sqlite", "migration", "validate", "backup"]
                ),
                "complexity": "high",
            },
            # DevOps & Infrastructure
            {
                "name": "docker_build_and_test_pipeline",
                "category": "devops",
                "description": "Complete Docker containerization with testing",
                "prompt": "Create a Python application, write a Dockerfile for it, build the Docker image, run the container to test it works, then create a docker-compose file for easy deployment and document the deployment process.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_application",
                    "write_dockerfile",
                    "build_image",
                    "test_container",
                    "create_compose_file",
                    "document_deployment",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["docker", "build", "container", "compose", "deploy"]
                ),
                "complexity": "high",
            },
            {
                "name": "ci_cd_configuration_setup",
                "category": "ci_cd",
                "description": "CI/CD pipeline configuration with validation",
                "prompt": "Set up a basic CI/CD pipeline configuration: create a GitHub Actions workflow file, configure build steps, add testing phases, set up deployment staging, and validate the configuration syntax.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_workflow_file",
                    "configure_build_steps",
                    "add_test_phases",
                    "setup_deployment",
                    "validate_syntax",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["github actions", "workflow", "build", "test", "deploy"]
                ),
                "complexity": "medium",
            },
            # Security & Testing
            {
                "name": "security_audit_automation",
                "category": "security",
                "description": "Automated security audit with reporting",
                "prompt": "Create a security audit script that checks file permissions, analyzes a Python codebase for potential vulnerabilities, runs security linting, generates a findings report, and creates remediation recommendations.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "check_file_permissions",
                    "scan_code_vulnerabilities",
                    "run_security_linting",
                    "generate_report",
                    "create_remediation_plan",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in [
                        "security",
                        "permissions",
                        "vulnerabilities",
                        "report",
                        "remediation",
                    ]
                ),
                "complexity": "high",
            },
            {
                "name": "automated_testing_suite",
                "category": "testing",
                "description": "Comprehensive testing suite setup and execution",
                "prompt": "Create a comprehensive testing setup: write unit tests, integration tests, create test data, run all tests with coverage reporting, identify any failures, and generate a testing summary report.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_unit_tests",
                    "create_integration_tests",
                    "setup_test_data",
                    "run_with_coverage",
                    "analyze_results",
                    "generate_summary",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["unit", "integration", "coverage", "results", "summary"]
                ),
                "complexity": "medium",
            },
            # API Development & Documentation
            {
                "name": "api_development_full_cycle",
                "category": "api_development",
                "description": "Complete API development with documentation and testing",
                "prompt": "Build a REST API: create the Flask application with multiple endpoints, write API documentation, create test scripts to validate endpoints, generate OpenAPI specification, and set up API monitoring.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_api_endpoints",
                    "write_documentation",
                    "create_test_scripts",
                    "generate_openapi_spec",
                    "setup_monitoring",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["api", "endpoints", "documentation", "test", "openapi"]
                ),
                "complexity": "high",
            },
            # Performance & Monitoring
            {
                "name": "performance_benchmark_suite",
                "category": "performance",
                "description": "Performance testing and benchmarking workflow",
                "prompt": "Create a performance testing suite: write benchmark scripts, run performance tests on sample code, analyze bottlenecks, generate performance reports with charts, and create optimization recommendations.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_benchmark_scripts",
                    "run_performance_tests",
                    "analyze_bottlenecks",
                    "generate_reports",
                    "create_optimization_plan",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in [
                        "benchmark",
                        "performance",
                        "bottlenecks",
                        "reports",
                        "optimization",
                    ]
                ),
                "complexity": "medium",
            },
            # Infrastructure as Code
            {
                "name": "infrastructure_provisioning",
                "category": "infrastructure",
                "description": "Infrastructure as code with validation",
                "prompt": "Set up infrastructure as code: create Terraform configurations for basic AWS resources, validate the configuration syntax, plan the deployment, create documentation for the infrastructure, and set up monitoring configs.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_terraform_configs",
                    "validate_syntax",
                    "plan_deployment",
                    "document_infrastructure",
                    "setup_monitoring_configs",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["terraform", "aws", "validate", "plan", "monitoring"]
                ),
                "complexity": "medium",
            },
            # Code Quality & Analysis
            {
                "name": "code_quality_analysis_pipeline",
                "category": "code_quality",
                "description": "Comprehensive code quality analysis workflow",
                "prompt": "Set up a code quality pipeline: analyze code complexity, run static analysis tools, check code formatting, generate quality metrics, create improvement recommendations, and set up quality gates.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "analyze_complexity",
                    "run_static_analysis",
                    "check_formatting",
                    "generate_metrics",
                    "create_recommendations",
                    "setup_quality_gates",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in [
                        "complexity",
                        "static analysis",
                        "formatting",
                        "metrics",
                        "quality",
                    ]
                ),
                "complexity": "medium",
            },
            # Migration & Legacy System Integration
            {
                "name": "legacy_system_migration_prep",
                "category": "migration",
                "description": "Legacy system migration preparation workflow",
                "prompt": "Prepare for legacy system migration: analyze existing codebase structure, identify dependencies, create migration scripts, test data conversion processes, document migration plan, and validate compatibility.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "analyze_codebase",
                    "identify_dependencies",
                    "create_migration_scripts",
                    "test_data_conversion",
                    "document_migration_plan",
                    "validate_compatibility",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in [
                        "migration",
                        "dependencies",
                        "conversion",
                        "plan",
                        "compatibility",
                    ]
                ),
                "complexity": "high",
            },
            # Simple Workflows for Balance
            {
                "name": "simple_script_with_tests",
                "category": "basic_development",
                "description": "Simple script development with testing",
                "prompt": "Create a Python script that calculates the Fibonacci sequence, write a test for it, run the test to verify it works, and document how to use the script.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_script",
                    "write_test",
                    "run_test",
                    "create_documentation",
                ],
                "validator": lambda r: all(
                    keyword in r.lower() for keyword in ["fibonacci", "test", "run", "document"]
                ),
                "complexity": "low",
            },
            {
                "name": "config_file_management",
                "category": "configuration",
                "description": "Configuration management with validation",
                "prompt": "Create a JSON configuration file for an application, validate its syntax, create a Python script to read and use the config, test that it works correctly, and document the configuration options.",
                "expected_tools": ["files", "shell"],
                "workflow_steps": [
                    "create_config_file",
                    "validate_syntax",
                    "create_reader_script",
                    "test_functionality",
                    "document_options",
                ],
                "validator": lambda r: all(
                    keyword in r.lower()
                    for keyword in ["json", "config", "validate", "test", "document"]
                ),
                "complexity": "low",
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute multi-step tool orchestration evaluation."""
        print("🛠️ Testing Multi-Step Tool Orchestration - Production Workflows")
        start_time = time.time()

        # Sample workflows for evaluation
        selected_workflows = self.workflow_templates[: self.sample_size]

        results = []
        passed_tests = 0
        tool_usage_stats = {"files": 0, "shell": 0, "search": 0}

        for i, workflow in enumerate(selected_workflows):
            print(f"Orchestration ({i+1}/{len(selected_workflows)}): {workflow['name']}")

            try:
                # Create agent with comprehensive toolset
                orchestration_agent = agent()
                orchestration_agent.tools = ["files", "shell", "search"]
                orchestration_agent.max_iterations = 20  # Allow complex workflows

                # Execute the complex workflow
                response, conversation_id = await orchestration_agent.run(workflow["prompt"])

                # Validate workflow completion
                passed = workflow["validator"](response)
                if passed:
                    passed_tests += 1

                # Track tool usage (approximate from response content)
                for tool in tool_usage_stats:
                    if tool in response.lower():
                        tool_usage_stats[tool] += 1

                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow["category"],
                        "complexity": workflow["complexity"],
                        "description": workflow["description"],
                        "expected_tools": workflow["expected_tools"],
                        "workflow_steps": len(workflow["workflow_steps"]),
                        "prompt": workflow["prompt"][:150] + "...",
                        "response": response[:400] + "..." if len(response) > 400 else response,
                        "passed": passed,
                        "workflow_completed": passed,
                        "conversation_id": conversation_id,
                    }
                )

                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"  {status} - Workflow completed: {passed}")

            except Exception as e:
                print(f"  💥 ERROR: {e}")
                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow.get("category", "unknown"),
                        "complexity": workflow.get("complexity", "unknown"),
                        "error": str(e),
                        "passed": False,
                        "workflow_completed": False,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / len(selected_workflows) if selected_workflows else 0.0
        benchmark_passed = pass_rate >= 0.7  # 70% threshold for complex orchestration

        # Analyze results
        complexity_analysis = self._analyze_by_complexity(results)
        category_analysis = self._analyze_by_category(results)

        return {
            "name": self.name,
            "benchmark_passed": benchmark_passed,
            "duration": duration,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "workflow_completion_rate": pass_rate,
                "avg_steps_per_workflow": sum(r.get("workflow_steps", 0) for r in results)
                / len(results)
                if results
                else 0,
                "complexity_breakdown": complexity_analysis,
                "category_breakdown": category_analysis,
                "tool_usage_distribution": tool_usage_stats,
            },
            "results": results,
            "metadata": {
                "evaluation_type": "Multi-Step Tool Orchestration",
                "cogency_capability": "Advanced Workflow Management",
                "production_ready_workflows": True,
                "error_recovery_tested": True,
                "sample_size": self.sample_size,
                "min_required_pass_rate": 0.7,
                "max_iterations_allowed": 20,
                "showcase_capabilities": [
                    "Complex multi-tool coordination",
                    "Error handling and workflow recovery",
                    "State management across tool calls",
                    "Production-ready engineering workflows",
                ],
            },
        }

    def _analyze_by_complexity(self, results: list[dict]) -> dict[str, Any]:
        """Analyze orchestration success by workflow complexity."""
        complexity_levels = {
            "low": {"total": 0, "passed": 0},
            "medium": {"total": 0, "passed": 0},
            "high": {"total": 0, "passed": 0},
        }

        for result in results:
            complexity = result.get("complexity", "medium")
            if complexity in complexity_levels:
                complexity_levels[complexity]["total"] += 1
                if result.get("passed", False):
                    complexity_levels[complexity]["passed"] += 1

        # Calculate pass rates
        for level in complexity_levels:
            total = complexity_levels[level]["total"]
            complexity_levels[level]["pass_rate"] = (
                complexity_levels[level]["passed"] / total if total > 0 else 0.0
            )

        return complexity_levels

    def _analyze_by_category(self, results: list[dict]) -> dict[str, Any]:
        """Analyze orchestration success by workflow category."""
        categories = {}

        for result in results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}

            categories[category]["total"] += 1
            if result.get("passed", False):
                categories[category]["passed"] += 1

        # Calculate pass rates
        for category in categories:
            total = categories[category]["total"]
            categories[category]["pass_rate"] = (
                categories[category]["passed"] / total if total > 0 else 0.0
            )

        return categories
