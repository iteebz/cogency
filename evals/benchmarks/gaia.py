"""GAIA benchmark evaluation (mini-bench: 50 examples per difficulty)."""

import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class GAIABenchmark:
    """GAIA (General AI Assistants) multi-step reasoning benchmark."""

    name = "gaia_benchmark"
    description = "GAIA mini-bench: 50 examples per difficulty level"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute GAIA benchmark evaluation."""
        from cogency import Agent

        print("🧠 Testing GAIA Benchmark...")
        start_time = time.time()

        # GAIA mini-bench: 50 examples across 3 difficulty levels
        test_cases = self._get_gaia_examples()

        # Agent with search and reasoning capabilities
        agent = Agent("gaia_tester", tools=["search", "files"], max_iterations=10)

        results = []
        total_tests = len(test_cases)
        passed_tests = 0

        for i, test_case in enumerate(test_cases):
            print(f"GAIA Level {test_case['level']} ({i+1}/{total_tests})...")

            try:
                response = await agent.run_async(test_case["question"])

                # Judge the quality of multi-step reasoning
                judge_result = await self._evaluate_gaia_response(test_case, response)

                # Log result
                self.logger.log_result(
                    eval_name=f"gaia_level_{test_case['level']}_{i+1}",
                    judge_result=judge_result,
                    agent_metadata={
                        "difficulty": test_case["level"],
                        "category": test_case["category"],
                    },
                    execution_time=0.0,
                )

                test_passed = judge_result.score.value >= 6.0
                if test_passed:
                    passed_tests += 1

                results.append(
                    {
                        "level": test_case["level"],
                        "category": test_case["category"],
                        "question": test_case["question"][:100] + "...",
                        "expected": test_case["expected_approach"],
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "score": judge_result.score.value,
                        "reasoning": judge_result.score.reasoning,
                        "passed": test_passed,
                    }
                )

                status = "✅ PASSED" if test_passed else "❌ FAILED"
                print(f"  {status} - Score: {judge_result.score.value}/10")

            except Exception as e:
                print(f"  💥 ERROR: {e}")
                results.append(
                    {
                        "level": test_case["level"],
                        "question": test_case["question"],
                        "error": str(e),
                        "passed": False,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        benchmark_passed = pass_rate >= 0.6  # 60% threshold for GAIA

        return {
            "name": self.name,
            "benchmark_passed": benchmark_passed,
            "duration": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "level_breakdown": self._analyze_by_level(results),
            },
            "results": results,
            "metadata": {
                "benchmark_type": "GAIA mini-bench",
                "difficulty_levels": [1, 2, 3],
                "examples_per_level": 17,  # ~50 total across 3 levels
                "min_required_score": 6.0,
                "logging_report": self.logger.generate_report(),
            },
        }

    def _get_gaia_examples(self) -> list[dict]:
        """GAIA mini-bench examples across difficulty levels."""
        return [
            # Level 1: Simple fact-finding (17 examples)
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What is the current population of Tokyo, Japan?",
                "expected_approach": "Direct search for current Tokyo population",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "Who won the Nobel Prize in Physics in 2023?",
                "expected_approach": "Search for 2023 Nobel Physics winner",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "If a product costs $99 and there's a 15% discount, what's the final price?",
                "expected_approach": "Basic percentage calculation",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What is the capital city of Australia?",
                "expected_approach": "Direct fact lookup",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "How many seconds are in 2 hours and 30 minutes?",
                "expected_approach": "Time unit conversion",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What is the chemical symbol for gold?",
                "expected_approach": "Basic chemistry knowledge",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "In which year was the World Wide Web invented?",
                "expected_approach": "Historical fact lookup",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "What is 15% of 240?",
                "expected_approach": "Percentage calculation",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What is the largest planet in our solar system?",
                "expected_approach": "Astronomy fact lookup",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "Who wrote the novel '1984'?",
                "expected_approach": "Literature fact lookup",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "If I save $50 per month, how much will I have saved in 2 years?",
                "expected_approach": "Simple multiplication",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What is the freezing point of water in Fahrenheit?",
                "expected_approach": "Temperature conversion knowledge",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "How many continents are there on Earth?",
                "expected_approach": "Geography knowledge",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "What is the area of a rectangle with length 8m and width 5m?",
                "expected_approach": "Basic geometry calculation",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "What does 'HTTP' stand for in web technology?",
                "expected_approach": "Technology acronym knowledge",
            },
            {
                "level": 1,
                "category": "fact_retrieval",
                "question": "Which element has the atomic number 1?",
                "expected_approach": "Chemistry periodic table knowledge",
            },
            {
                "level": 1,
                "category": "calculation",
                "question": "If a train travels 60 km/h for 3 hours, how far does it go?",
                "expected_approach": "Distance = speed × time",
            },
            # Level 2: Multi-step reasoning (17 examples)
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "Find the current CEO of Apple and tell me their educational background.",
                "expected_approach": "Search Apple CEO, then research their education",
            },
            {
                "level": 2,
                "category": "analysis",
                "question": "Compare the GDP per capita of France and Germany. Which is higher and by how much?",
                "expected_approach": "Look up both GDPs, calculate per capita, compare",
            },
            {
                "level": 2,
                "category": "temporal_reasoning",
                "question": "If it's currently 3:30 PM in New York, what time is it in Tokyo right now?",
                "expected_approach": "Calculate time zone difference and convert",
            },
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "What was the box office total for the highest-grossing movie of 2022, and who directed it?",
                "expected_approach": "Find top 2022 movie, then research director and earnings",
            },
            {
                "level": 2,
                "category": "calculation_with_research",
                "question": "Find the current Bitcoin price and calculate how much $1000 would buy in Bitcoin.",
                "expected_approach": "Look up Bitcoin price, then calculate $1000 worth",
            },
            {
                "level": 2,
                "category": "analysis",
                "question": "Which programming language is more popular according to recent surveys: Python or Java?",
                "expected_approach": "Research recent programming language popularity surveys",
            },
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "Find the winner of the 2023 Formula 1 World Championship and their nationality.",
                "expected_approach": "Research F1 2023 winner, then find their nationality",
            },
            {
                "level": 2,
                "category": "temporal_reasoning",
                "question": "How many days are there between Christmas 2023 and New Year's Day 2024?",
                "expected_approach": "Calculate date difference between Dec 25 and Jan 1",
            },
            {
                "level": 2,
                "category": "analysis",
                "question": "Which social media platform has more monthly active users: Instagram or TikTok?",
                "expected_approach": "Research current user statistics for both platforms",
            },
            {
                "level": 2,
                "category": "calculation_with_research",
                "question": "Find the current population of Canada and calculate the population density (people per km²).",
                "expected_approach": "Look up Canada's population and area, calculate density",
            },
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "What is the most recent iPhone model and what is its starting price in USD?",
                "expected_approach": "Research latest iPhone model and pricing",
            },
            {
                "level": 2,
                "category": "analysis",
                "question": "Between Tesla and Toyota, which company sold more electric vehicles in 2023?",
                "expected_approach": "Research EV sales data for both companies in 2023",
            },
            {
                "level": 2,
                "category": "temporal_reasoning",
                "question": "If someone was born in 1995, how old will they be in 2030?",
                "expected_approach": "Calculate age difference: 2030 - 1995",
            },
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "Find the current world record holder for men's 100m sprint and their record time.",
                "expected_approach": "Research current 100m world record and holder",
            },
            {
                "level": 2,
                "category": "calculation_with_research",
                "question": "What is the current exchange rate from USD to EUR, and how many euros is $500?",
                "expected_approach": "Look up USD/EUR rate, calculate $500 in euros",
            },
            {
                "level": 2,
                "category": "analysis",
                "question": "Which country has a higher life expectancy: South Korea or Japan?",
                "expected_approach": "Research life expectancy data for both countries",
            },
            {
                "level": 2,
                "category": "multi_step_research",
                "question": "Find the current Secretary-General of the United Nations and when they started their term.",
                "expected_approach": "Research current UN Secretary-General and term start date",
            },
            # Level 3: Complex multi-step reasoning (16 examples)
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Research the top 3 renewable energy companies by market cap. For each, find their primary technology focus and latest major project announcement.",
                "expected_approach": "Multi-step: find top renewable companies, research each company's focus and recent projects",
            },
            {
                "level": 3,
                "category": "synthesis",
                "question": "Compare the climate change policies of the US, EU, and China. What are the key similarities and differences in their approaches?",
                "expected_approach": "Research each region's climate policies, then synthesize comparisons",
            },
            {
                "level": 3,
                "category": "complex_calculation",
                "question": "If global CO2 emissions are currently 36 billion tons per year and need to reach net zero by 2050, what percentage reduction is needed annually?",
                "expected_approach": "Research current emissions, calculate required annual reduction rate",
            },
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Analyze the impact of AI on employment in the tech sector over the past 2 years. What are the main trends?",
                "expected_approach": "Research AI's employment impact, analyze trends, synthesize findings",
            },
            {
                "level": 3,
                "category": "synthesis",
                "question": "What are the main arguments for and against cryptocurrency adoption by central banks? Provide a balanced analysis.",
                "expected_approach": "Research CBDC arguments, present balanced pro/con analysis",
            },
            {
                "level": 3,
                "category": "complex_calculation",
                "question": "Calculate the total cost of charging an electric vehicle annually if you drive 15,000 miles, get 3.5 miles/kWh efficiency, and electricity costs $0.12/kWh.",
                "expected_approach": "Multi-step calculation: miles → kWh → annual cost",
            },
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Research the current state of quantum computing commercialization. Which companies are leading and what are their main applications?",
                "expected_approach": "Research quantum computing market, identify leaders and applications",
            },
            {
                "level": 3,
                "category": "synthesis",
                "question": "How has the war in Ukraine affected global food security? What are the main supply chain disruptions?",
                "expected_approach": "Research Ukraine war's food security impact, analyze disruptions",
            },
            {
                "level": 3,
                "category": "complex_calculation",
                "question": "If the world's population grows from 8 billion to 9.7 billion by 2050, and food production needs to increase 50%, what's the required annual growth rate in food production?",
                "expected_approach": "Calculate compound annual growth rate needed for food production",
            },
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Evaluate the effectiveness of different COVID-19 vaccine distribution strategies used by various countries. What worked best?",
                "expected_approach": "Research vaccine strategies by country, analyze effectiveness",
            },
            {
                "level": 3,
                "category": "synthesis",
                "question": "What are the main technological challenges in achieving fully autonomous vehicles, and which companies are closest to solving them?",
                "expected_approach": "Research autonomous vehicle challenges, assess company progress",
            },
            {
                "level": 3,
                "category": "complex_calculation",
                "question": "Calculate the potential carbon footprint reduction if 50% of global shipping switched from heavy fuel oil to green ammonia fuel.",
                "expected_approach": "Research shipping emissions, ammonia fuel benefits, calculate reduction",
            },
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Analyze the geopolitical implications of the US CHIPS Act. How are other countries responding to this semiconductor policy?",
                "expected_approach": "Research CHIPS Act, analyze global semiconductor policy responses",
            },
            {
                "level": 3,
                "category": "synthesis",
                "question": "What are the main ethical concerns around AI-generated content, and how are different platforms and governments addressing them?",
                "expected_approach": "Research AI content ethics, analyze platform and government responses",
            },
            {
                "level": 3,
                "category": "complex_calculation",
                "question": "If global internet traffic grows 25% annually, how much bandwidth infrastructure investment is needed to support this growth over 5 years?",
                "expected_approach": "Research current traffic, calculate growth projections, estimate infrastructure needs",
            },
            {
                "level": 3,
                "category": "complex_analysis",
                "question": "Research the current state of nuclear fusion energy development. What are the main technical milestones achieved in 2023-2024?",
                "expected_approach": "Research recent fusion developments, identify key milestones",
            },
        ]

    async def _evaluate_gaia_response(self, test_case: dict, response: str):
        """Evaluate GAIA benchmark response quality."""

        criteria = f"""GAIA Benchmark Assessment - Level {test_case['level']}:

Question: {test_case['question']}
Expected Approach: {test_case['expected_approach']}
Category: {test_case['category']}

Rate the agent's multi-step reasoning and information synthesis:

1. **Information Gathering**: Did it collect relevant, accurate information?
2. **Reasoning Quality**: Was the logical process sound and well-structured?
3. **Answer Completeness**: Did it fully address all parts of the question?
4. **Accuracy**: Are the facts and calculations correct?

Level {test_case['level']} Expectations:
- Level 1: Direct fact-finding with basic verification
- Level 2: Multi-step research with logical connections
- Level 3: Complex analysis with synthesis across multiple sources

Score 1-3: Incorrect facts or fundamentally flawed reasoning
Score 4-6: Partial success with some reasoning or accuracy issues
Score 7-8: Good reasoning with minor gaps or inaccuracies
Score 9-10: Excellent multi-step reasoning with accurate, complete analysis"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=test_case["question"],
            criteria=criteria,
            context={
                "benchmark": "GAIA",
                "difficulty_level": test_case["level"],
                "category": test_case["category"],
                "expected_approach": test_case["expected_approach"],
            },
        )

    def _analyze_by_level(self, results: list) -> dict:
        """Analyze results by difficulty level."""
        level_stats = {
            1: {"total": 0, "passed": 0},
            2: {"total": 0, "passed": 0},
            3: {"total": 0, "passed": 0},
        }

        for result in results:
            if "level" in result:
                level = result["level"]
                level_stats[level]["total"] += 1
                if result.get("passed", False):
                    level_stats[level]["passed"] += 1

        for level in level_stats:
            if level_stats[level]["total"] > 0:
                level_stats[level]["pass_rate"] = (
                    level_stats[level]["passed"] / level_stats[level]["total"]
                )
            else:
                level_stats[level]["pass_rate"] = 0.0

        return level_stats
