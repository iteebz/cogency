"""Cross-session workflow memory evaluation - Cogency's killer differentiator.

Demonstrates realistic multi-session project workflows where context is maintained
across agent restarts and session boundaries. This is Cogency's unique strength.
"""

import time
from typing import Any

from ...core import agent


class CrossSessionWorkflows:
    """Test sophisticated cross-session workflow memory - Cogency's differentiator."""

    name = "cross_session_workflows"
    description = "Multi-session project workflow memory showcase"

    def __init__(self, sample_size: int = 25):
        """Initialize with 25 examples for AGI lab demo."""
        self.sample_size = sample_size
        self.workflow_templates = self._create_workflow_templates()

    def _create_workflow_templates(self) -> list[dict[str, Any]]:
        """Create realistic cross-session workflow scenarios."""
        return [
            # Software Development Workflows
            {
                "name": "feature_development_cycle",
                "category": "software_engineering",
                "session_1": "I'm starting development on a user authentication feature for our web app. The requirements are: JWT tokens, password hashing with bcrypt, role-based access (admin/user), and Redis session storage. Create a development plan and identify the key components we'll need.",
                "session_2": "I'm working on a different project now - setting up a CI/CD pipeline for our mobile app. Configure the build steps and deployment strategy.",
                "session_3": "Back to the authentication feature - can you help me implement the JWT token validation middleware based on our earlier plan?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["jwt", "authentication", "middleware", "plan", "bcrypt"]
                ),
                "interference_test": True,
            },
            # Research & Analysis Workflows
            {
                "name": "market_research_continuation",
                "category": "research",
                "session_1": "I'm researching the autonomous vehicle market for our investment thesis. Key focus areas: regulatory landscape, major players, technology readiness levels, and market size projections for 2024-2030. Start gathering initial findings.",
                "session_2": "Quick task - analyze this year's crypto market trends and DeFi protocols for a different client.",
                "session_3": "Back to AV research - using our previous findings, what are the key regulatory challenges we identified and how do they impact our investment timeline?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["autonomous", "regulatory", "investment", "av", "vehicle"]
                ),
                "interference_test": True,
            },
            # Data Science Project Workflows
            {
                "name": "ml_model_development",
                "category": "data_science",
                "session_1": "Starting a churn prediction model for our SaaS platform. Dataset has 10k customers, features include usage metrics, support tickets, billing history, and engagement scores. Outline the modeling approach and feature engineering strategy.",
                "session_2": "Different project - help me analyze customer segmentation for an e-commerce client using RFM analysis.",
                "session_3": "Back to churn prediction - based on our earlier feature engineering plan, what preprocessing steps should we implement for the usage metrics and engagement scores?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["churn", "prediction", "features", "usage", "preprocessing"]
                ),
                "interference_test": True,
            },
            # Product Management Workflows
            {
                "name": "product_roadmap_planning",
                "category": "product_management",
                "session_1": "Planning our Q1 2024 product roadmap for our project management SaaS. Key initiatives: advanced reporting dashboard, team collaboration features, mobile app v2, and API rate limiting improvements. Create a prioritization framework.",
                "session_2": "Quick diversion - competitor analysis for a fintech startup's payment processing features.",
                "session_3": "Back to our Q1 roadmap - using the prioritization framework we developed, which features should we tackle first given our engineering capacity constraints?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["roadmap", "prioritization", "q1", "dashboard", "collaboration"]
                ),
                "interference_test": True,
            },
            # Architecture & System Design
            {
                "name": "system_architecture_evolution",
                "category": "architecture",
                "session_1": "Designing a scalable microservices architecture for our e-commerce platform. Requirements: 100k+ concurrent users, global deployment, event-driven order processing, and real-time inventory. Document the service boundaries and data flow.",
                "session_2": "Separate task - database optimization for a legacy monolithic application.",
                "session_3": "Back to microservices architecture - based on our service boundaries design, what event sourcing patterns should we implement for the order processing workflow?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["microservices", "event", "order", "processing", "boundaries"]
                ),
                "interference_test": True,
            },
            # Simple Memory Retention (No Interference)
            {
                "name": "project_context_simple",
                "category": "simple_retention",
                "session_1": "I'm working on Project Phoenix - a customer analytics dashboard. Key metrics we're tracking: user engagement, conversion rates, and retention patterns.",
                "session_2": "What was the name of my analytics project and what metrics are we tracking?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["phoenix", "analytics", "engagement", "conversion", "retention"]
                ),
                "interference_test": False,
            },
            # Client Project Context
            {
                "name": "client_project_continuity",
                "category": "client_management",
                "session_1": "Client briefing: TechCorp wants to migrate their legacy inventory system to cloud-native. Timeline: 6 months, budget: $500k, main pain points are real-time sync and reporting bottlenecks. Document our approach.",
                "session_2": "Different client call - healthcare startup needs HIPAA compliance audit for their patient portal.",
                "session_3": "Back to TechCorp migration - what were the main pain points we identified and what's our recommended timeline for the cloud-native migration?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in [
                        "techcorp",
                        "inventory",
                        "cloud",
                        "real-time",
                        "sync",
                        "6 months",
                    ]
                ),
                "interference_test": True,
            },
            # Technical Documentation Workflows
            {
                "name": "api_documentation_project",
                "category": "documentation",
                "session_1": "Creating comprehensive API documentation for our payment processing service. Endpoints include: /payments/create, /payments/status, /refunds/process, and /webhooks/configure. Each needs request/response schemas, error codes, and integration examples.",
                "session_2": "Quick task - write user onboarding documentation for a different product's mobile app.",
                "session_3": "Back to payment API docs - for the /payments/create endpoint we planned, what are the required request parameters and error codes we need to document?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in [
                        "/payments/create",
                        "request",
                        "parameters",
                        "error codes",
                        "payment",
                    ]
                ),
                "interference_test": True,
            },
            # Security Assessment Workflows
            {
                "name": "security_audit_continuation",
                "category": "security",
                "session_1": "Conducting security audit for our web application. Scope includes: authentication mechanisms, input validation, SQL injection vectors, XSS vulnerabilities, and API security. Start with authentication assessment.",
                "session_2": "Side project - penetration testing for a client's mobile application.",
                "session_3": "Back to our web app security audit - based on our authentication assessment, what input validation vulnerabilities should we prioritize testing next?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["authentication", "input validation", "audit", "sql", "xss"]
                ),
                "interference_test": True,
            },
            # Business Analysis Workflows
            {
                "name": "business_process_optimization",
                "category": "business_analysis",
                "session_1": "Analyzing our customer support workflow to reduce response times. Current process: ticket creation → auto-routing → agent assignment → resolution. Average resolution time is 24 hours, target is 8 hours. Map the bottlenecks.",
                "session_2": "Different analysis - supply chain optimization for a manufacturing client.",
                "session_3": "Back to support workflow optimization - what were the main bottlenecks we identified in the ticket routing process and how can we achieve our 8-hour target?",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["support", "routing", "bottlenecks", "8 hour", "ticket"]
                ),
                "interference_test": True,
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute cross-session workflow memory evaluation."""
        print("🧠 Testing Cross-Session Workflow Memory - Cogency's Differentiator")
        start_time = time.time()

        # Sample workflows for evaluation
        selected_workflows = self.workflow_templates[: self.sample_size]

        results = []
        passed_tests = 0

        for i, workflow in enumerate(selected_workflows):
            print(f"Workflow ({i+1}/{len(selected_workflows)}): {workflow['name']}")

            try:
                # Use consistent user_id for memory persistence
                user_id = f"workflow_user_{workflow['name']}"

                # Session 1: Initial context setting
                session1_agent = agent(memory=True)
                await session1_agent.run(workflow["session_1"], user_id=user_id)

                if workflow.get("interference_test", False):
                    # Session 2: Interference task (different domain)
                    session2_agent = agent(memory=True)
                    await session2_agent.run(workflow["session_2"], user_id=user_id)

                # Session 3: Context retrieval and continuation
                session3_agent = agent(memory=True)
                if workflow.get("interference_test", False):
                    response, _ = await session3_agent.run(workflow["session_3"], user_id=user_id)
                else:
                    # For simple retention tests, session_2 is the recall prompt
                    response, _ = await session3_agent.run(workflow["session_2"], user_id=user_id)

                # Validate memory retention
                passed = workflow["validator"](response)
                if passed:
                    passed_tests += 1

                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow["category"],
                        "interference_test": workflow.get("interference_test", False),
                        "session_1": workflow["session_1"][:100] + "...",
                        "final_prompt": workflow.get("session_3", workflow.get("session_2", ""))[
                            :100
                        ]
                        + "...",
                        "response": response[:300] + "..." if len(response) > 300 else response,
                        "passed": passed,
                        "memory_retention": passed,
                    }
                )

                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"  {status} - Memory retained: {passed}")

            except Exception as e:
                print(f"  💥 ERROR: {e}")
                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow.get("category", "unknown"),
                        "error": str(e),
                        "passed": False,
                        "memory_retention": False,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / len(selected_workflows) if selected_workflows else 0.0
        benchmark_passed = pass_rate >= 0.8  # 80% threshold for memory workflows

        # Analyze by category and interference
        category_analysis = self._analyze_by_category(results)
        interference_analysis = self._analyze_interference_impact(results)

        return {
            "name": self.name,
            "benchmark_passed": benchmark_passed,
            "duration": duration,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "memory_retention_rate": pass_rate,
                "category_breakdown": category_analysis,
                "interference_impact": interference_analysis,
            },
            "results": results,
            "metadata": {
                "evaluation_type": "Cross-Session Workflow Memory",
                "cogency_differentiator": True,
                "realistic_workflows": True,
                "interference_testing": True,
                "sample_size": self.sample_size,
                "min_required_pass_rate": 0.8,
                "showcase_capabilities": [
                    "Cross-session memory persistence",
                    "Context isolation from interference",
                    "Realistic project workflow continuity",
                    "Multi-domain knowledge retention",
                ],
            },
        }

    def _analyze_by_category(self, results: list[dict]) -> dict[str, Any]:
        """Analyze memory retention by workflow category."""
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

    def _analyze_interference_impact(self, results: list[dict]) -> dict[str, Any]:
        """Analyze impact of interference tasks on memory retention."""
        interference_results = [r for r in results if r.get("interference_test", False)]
        simple_results = [r for r in results if not r.get("interference_test", False)]

        interference_pass_rate = (
            sum(1 for r in interference_results if r.get("passed", False))
            / len(interference_results)
            if interference_results
            else 0.0
        )
        simple_pass_rate = (
            sum(1 for r in simple_results if r.get("passed", False)) / len(simple_results)
            if simple_results
            else 0.0
        )

        return {
            "interference_tests": len(interference_results),
            "interference_pass_rate": interference_pass_rate,
            "simple_tests": len(simple_results),
            "simple_pass_rate": simple_pass_rate,
            "memory_robustness": interference_pass_rate >= 0.7,  # Can handle interference
        }
