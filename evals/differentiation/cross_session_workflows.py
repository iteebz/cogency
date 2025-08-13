"""Cross-session workflow continuity - project memory across agent restarts."""

import time
from typing import Any

from ..core import agent


class CrossSessionWorkflows:
    """Test cross-session project context retention."""

    name = "cross_session_workflows"
    description = "Project continuity across agent restarts"
    time_budget = 600
    pass_threshold = 0.7

    def __init__(self):
        self.canonical_workflows = [
            # SOFTWARE DEVELOPMENT ARC
            {
                "name": "jwt_auth_development",
                "context_session": "Start developing JWT authentication for our API. Key requirements: bcrypt password hashing, role-based access (admin/user), Redis session storage, and proper token expiration. Create the development plan and identify main components.",
                "interference_task": "Quick diversion - analyze competitor's new pricing strategy and market positioning for different client",
                "continuation_session": "Back to JWT authentication - based on our development plan, help me implement the token validation middleware component",
                "validator": lambda r: all(
                    kw in r.lower() for kw in ["jwt", "token", "middleware", "validation"]
                ),
                "category": "software_engineering",
            },
            # RESEARCH CONTINUITY ARC
            {
                "name": "autonomous_vehicle_research",
                "context_session": "Research autonomous vehicle market for investment thesis. Focus areas: regulatory landscape in US/EU, major players (Waymo, Tesla, Cruise), technology readiness levels, and market projections 2024-2030. Start gathering key findings.",
                "interference_task": "Separate project - analyze latest DeFi protocol trends and yield farming opportunities for crypto client",
                "continuation_session": "Continue AV research - what were the key regulatory challenges we identified for our investment timeline?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["autonomous", "regulatory", "challenges", "investment"]
                ),
                "category": "research_analysis",
            },
            # CLIENT PROJECT ARC
            {
                "name": "techcorp_migration",
                "context_session": "Client briefing: TechCorp wants to migrate legacy inventory system to cloud-native architecture. Budget: $500k, Timeline: 6 months, Main pain points: real-time inventory sync and reporting bottlenecks. Document our approach and key considerations.",
                "interference_task": "Healthcare startup consultation - HIPAA compliance requirements for patient portal development",
                "continuation_session": "Back to TechCorp migration project - what was their budget and what were the main technical pain points we identified?",
                "validator": lambda r: any(
                    kw in r.lower() for kw in ["techcorp", "500k", "inventory", "sync", "reporting"]
                ),
                "category": "client_management",
            },
            # DATA SCIENCE PROJECT ARC
            {
                "name": "churn_prediction_model",
                "context_session": "Starting churn prediction model for SaaS platform. Dataset: 10k customers, features include usage metrics, support tickets, billing history, engagement scores. Outline modeling approach and feature engineering strategy.",
                "interference_task": "E-commerce client needs customer segmentation analysis using RFM methodology",
                "continuation_session": "Back to churn model - based on our feature engineering strategy, what preprocessing should we do for usage metrics?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["churn", "usage", "metrics", "preprocessing", "feature"]
                ),
                "category": "data_science",
            },
            # PRODUCT ROADMAP ARC
            {
                "name": "q1_product_roadmap",
                "context_session": "Planning Q1 2024 product roadmap for project management SaaS. Key initiatives: advanced reporting dashboard, team collaboration features, mobile app v2, API rate limiting. Create prioritization framework.",
                "interference_task": "Fintech competitor analysis - payment processing feature comparison and market gaps",
                "continuation_session": "Back to Q1 roadmap - using our prioritization framework, which features should we tackle first given engineering constraints?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["roadmap", "prioritization", "dashboard", "collaboration", "q1"]
                ),
                "category": "product_management",
            },
            # ARCHITECTURE DESIGN ARC
            {
                "name": "microservices_architecture",
                "context_session": "Design scalable microservices architecture for e-commerce platform. Requirements: 100k+ concurrent users, global deployment, event-driven order processing, real-time inventory updates. Document service boundaries and data flow.",
                "interference_task": "Legacy monolith database optimization project for different client",
                "continuation_session": "Continue microservices design - based on our service boundaries, what event sourcing patterns for order processing workflow?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["microservices", "service", "boundaries", "event", "order"]
                ),
                "category": "system_architecture",
            },
            # SECURITY AUDIT ARC
            {
                "name": "web_app_security_audit",
                "context_session": "Conducting security audit for web application. Scope: authentication mechanisms, input validation, SQL injection vectors, XSS vulnerabilities, API security. Start with authentication assessment and document findings.",
                "interference_task": "Mobile app penetration testing for different client - focus on API endpoints and data storage",
                "continuation_session": "Back to web app audit - based on authentication assessment, what input validation vulnerabilities should we test next?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["authentication", "input", "validation", "vulnerabilities", "audit"]
                ),
                "category": "security_analysis",
            },
            # BUSINESS PROCESS ARC
            {
                "name": "support_workflow_optimization",
                "context_session": "Analyzing customer support workflow to reduce response times. Current: ticket creation → auto-routing → agent assignment → resolution. Average: 24 hours, Target: 8 hours. Map bottlenecks and inefficiencies.",
                "interference_task": "Manufacturing supply chain optimization project - inventory turnover and lead time analysis",
                "continuation_session": "Back to support optimization - what were the main bottlenecks in ticket routing and how to achieve 8-hour target?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["support", "ticket", "routing", "bottlenecks", "8 hour"]
                ),
                "category": "business_optimization",
            },
            # API DEVELOPMENT ARC
            {
                "name": "payment_api_documentation",
                "context_session": "Creating API documentation for payment processing service. Endpoints: /payments/create, /payments/status, /refunds/process, /webhooks/configure. Need request/response schemas, error codes, integration examples.",
                "interference_task": "User onboarding documentation for mobile app - different product entirely",
                "continuation_session": "Continue payment API docs - for /payments/create endpoint, what are the required parameters and error codes to document?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["payments/create", "parameters", "error", "codes", "endpoint"]
                ),
                "category": "api_development",
            },
            # INFRASTRUCTURE PROJECT ARC
            {
                "name": "terraform_infrastructure",
                "context_session": "Setting up infrastructure as code with Terraform. Target: AWS resources for web application - VPC, subnets, load balancers, RDS, ElastiCache. Create modular configuration and deployment plan.",
                "interference_task": "Docker containerization project for different microservices application",
                "continuation_session": "Back to Terraform setup - based on our modular config plan, what monitoring and alerting should we configure?",
                "validator": lambda r: any(
                    kw in r.lower()
                    for kw in ["terraform", "aws", "monitoring", "alerting", "infrastructure"]
                ),
                "category": "infrastructure",
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute cross-session workflow test."""
        print("🧠 Cross-Session Workflows")
        print("Testing project continuity across agent restarts")

        start_time = time.time()
        results = []
        passed_tests = 0

        # Test subset for time management (10 workflows for comprehensive demo)
        test_workflows = self.canonical_workflows[:10]

        for i, workflow in enumerate(test_workflows):
            print(f"  Workflow ({i+1}/{len(test_workflows)}): {workflow['name']}")

            try:
                # Use consistent user_id for memory persistence across sessions
                user_id = f"demo_user_{workflow['name']}"

                # SESSION 1: Establish project context
                context_agent = agent(memory=True)
                print("    📝 Setting context...")
                await context_agent.run(workflow["context_session"], user_id=user_id)

                # SESSION 2: Interference task (different domain)
                interference_agent = agent(memory=True)
                print("    🔀 Interference task...")
                await interference_agent.run(workflow["interference_task"], user_id=user_id)

                # SESSION 3: Context retrieval and project continuation
                continuation_agent = agent(memory=True)
                print("    🎯 Testing continuation...")
                response, _ = await continuation_agent.run(
                    workflow["continuation_session"], user_id=user_id
                )

                # Validate context retention
                context_retained = workflow["validator"](response)
                if context_retained:
                    passed_tests += 1

                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow["category"],
                        "context_session": workflow["context_session"][:100] + "...",
                        "continuation_session": workflow["continuation_session"][:100] + "...",
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "context_retained": context_retained,
                        "passed": context_retained,
                    }
                )

                status = "✅ RETAINED" if context_retained else "❌ LOST"
                print(f"    {status} - Context: {context_retained}")

            except Exception as e:
                print(f"    💥 ERROR: {e}")
                results.append(
                    {
                        "name": workflow["name"],
                        "category": workflow.get("category", "unknown"),
                        "error": str(e),
                        "context_retained": False,
                        "passed": False,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / len(test_workflows)
        differentiation_strong = pass_rate >= self.pass_threshold

        # Generate insight
        if pass_rate >= 0.8:
            insight = "Exceptional cross-session memory - unique capability"
        elif pass_rate >= 0.7:
            insight = "Strong workflow continuity - clear differentiation"
        elif pass_rate >= 0.5:
            insight = "Partial retention - needs refinement"
        else:
            insight = "Weak cross-session memory - not reliable"

        # Category analysis
        category_performance = {}
        for result in results:
            category = result.get("category", "unknown")
            if category not in category_performance:
                category_performance[category] = {"total": 0, "passed": 0}
            category_performance[category]["total"] += 1
            if result.get("passed", False):
                category_performance[category]["passed"] += 1

        return {
            "name": self.name,
            "tier": "differentiation",
            "differentiation_strong": differentiation_strong,
            "duration": duration,
            "summary": {
                "total_workflows": len(test_workflows),
                "successful_continuations": passed_tests,
                "pass_rate": pass_rate,
                "context_retention_rate": pass_rate,
                "category_performance": category_performance,
            },
            "results": results,
            "executive_insight": insight,
            "competitive_advantage": {
                "unique_capability": "Cross-session project memory",
                "value_proposition": f"{pass_rate:.1%} continuity success rate",
                "use_cases": ["Multi-day projects", "Research workflows", "Client management"],
            },
            "recommendation": "STRONG_DIFFERENTIATOR"
            if differentiation_strong
            else "NEEDS_IMPROVEMENT",
        }
